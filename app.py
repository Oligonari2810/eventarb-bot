#!/usr/bin/env python3
"""
EventArb Bot - Aplicación principal
Bot para automatizar eventos y notificaciones
"""

import gc
import logging
import logging.handlers
import os
import sqlite3
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional

# FIX DE EMERGENCIA: Restaurar streams si están rotos
try:
    sys.stdout.fileno()
except Exception:
    try:
        sys.stdout = open("/dev/stdout", "w")
        sys.stderr = open("/dev/stderr", "w")
    except Exception:
        # Fallback: usar archivos locales
        sys.stdout = open("logs/stdout_fix.log", "w")
        sys.stderr = open("logs/stderr_fix.log", "w")


# LIMPIEZA DE ESTADO DE BINANCE
def clean_binance_state():
    """Limpia objetos de Binance que puedan estar corrompiendo streams"""
    try:
        for obj in gc.get_objects():
            if "binance" in str(type(obj)).lower():
                try:
                    if hasattr(obj, "close"):
                        obj.close()
                except Exception:
                    pass
        gc.collect()  # Forzar garbage collection
    except Exception:
        # Si falla la limpieza, continuar
        pass


# Ejecutar limpieza al inicio
clean_binance_state()

import yaml
from dotenv import load_dotenv

# Configurar logging robusto ANTES de cualquier import
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def setup_robust_logger(name, log_file):
    """Configura logger robusto con rotación automática"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evitar handlers duplicados
    if logger.handlers:
        return logger

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5_000_000, backupCount=5, delay=True, encoding="utf-8"  # 5MB
    )

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Configurar logger principal de la app
app_logger = setup_robust_logger("bot_app", "logs/app.log")


# FUNCIONES HELPER PARA CONVERSIÓN MONETARIA
def decimal_to_cents(amount: Decimal) -> int:
    """Convierte Decimal a centavos (integer)"""
    return int(amount * 100)


def cents_to_decimal(cents: int) -> Decimal:
    """Convierte centavos (integer) a Decimal"""
    return Decimal(cents) / 100


def check_emergency_stop() -> bool:
    """Verifica si el bot debe detenerse por emergencia"""
    try:
        conn = sqlite3.connect("trades.db")
        cursor = conn.execute(
            "SELECT emergency_stop FROM bot_state WHERE date = date('now')"
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            app_logger.critical(
                "🚨 EMERGENCY_STOP ACTIVADO - Bot detenido por seguridad"
            )
            return True
        return False

    except Exception:
        app_logger.error("Error verificando emergency_stop")
        return False  # En caso de error, permitir operación


def update_bot_state(
    trades_done: Optional[int] = None, loss_cents: Optional[int] = None
):
    """Actualiza el estado del bot en la base de datos"""
    try:
        conn = sqlite3.connect("trades.db")
        today = datetime.now().strftime("%Y-%m-%d")

        if trades_done is not None:
            conn.execute(
                """
                UPDATE bot_state SET trades_done = ?, last_updated = datetime('now')
                WHERE date = ?
            """,
                (trades_done, today),
            )

        if loss_cents is not None:
            conn.execute(
                """
                UPDATE bot_state SET loss_cents = ?, last_updated = datetime('now')
                WHERE date = ?
            """,
                (loss_cents, today),
            )

        conn.commit()
        conn.close()

    except Exception:
        app_logger.error("Error actualizando bot_state")


from eventarb.core.logging_setup import setup_logging
from eventarb.core.planner import plan_actions_for_event
from eventarb.core.risk_manager import RiskManager
from eventarb.exec.order_router import OrderRouter
from eventarb.exec.sl_tp_manager import SLTPManager
from eventarb.ingest.sheets_reader import read_events_from_sheet
from eventarb.integrations.google_sheets_logger import sheets_logger
from eventarb.metrics.oco_metrics import OCOMetrics
from eventarb.notify.telegram_stub import send_telegram
from eventarb.storage.repository import init_db, insert_trade


class DailyLimits:
    def __init__(self):
        self.daily_max_loss_pct = Decimal(os.getenv("DAILY_MAX_LOSS_PCT", "5.0"))
        self.daily_max_trades = int(os.getenv("DAILY_MAX_TRADES", "20"))
        self.today_trades = 0
        self.today_pnl = Decimal("0.0")

    def can_trade(self) -> bool:
        """Check if daily limits allow trading"""
        if self.today_trades >= self.daily_max_trades:
            print(
                f"Daily trade limit reached ({self.today_trades}/{self.daily_max_trades})"
            )
            return False

        if self.today_pnl <= -self.daily_max_loss_pct:
            print(
                f"Daily loss limit reached ({self.today_pnl:.2f}%/-{self.daily_max_loss_pct}%)"
            )
            return False

        return True

    def record_trade(self, estimated_pnl: float = 0.0):
        """Record trade and update daily metrics"""
        self.today_trades += 1
        self.today_pnl += estimated_pnl

    def today_loss_pct(self) -> float:
        """Calculate actual daily loss percentage from database"""
        try:
            conn = sqlite3.connect(os.getenv("DB_PATH", "trades.db"))
            cursor = conn.cursor()

            # Get today's trade count
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM trades WHERE DATE(created_at) = ?", (today,)
            )
            self.today_trades = cursor.fetchone()[0]

            # For now, return 0 since we don't have pnl_usd column yet
            # This will be updated when we add the proper PnL tracking
            return 0.0

        except Exception:
            print("Error calculating today_loss_pct")
            return 0.0

    def update_from_database(self):
        """Update daily metrics from actual database data"""
        try:
            conn = sqlite3.connect(os.getenv("DB_PATH", "trades.db"))
            cursor = conn.cursor()

            # Get today's trade count
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM trades WHERE DATE(created_at) = ?", (today,)
            )
            self.today_trades = cursor.fetchone()[0]

            # Get today's actual PnL
            self.today_pnl = self.today_loss_pct()

            conn.close()

        except Exception:
            print("Error updating from database")


def _env_float(name: str, default: float) -> float:
    """Get environment variable as float with fallback"""
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def _today_str_local() -> str:
    """Get today's date in local timezone"""
    # Uses system TZ; if you want to force America/Chicago, export TZ=America/Chicago before starting
    return datetime.now().date().isoformat()


def today_loss_pct(db_path: str = "trades.db") -> float:
    """
    Calcula la pérdida REALIZADA de HOY como porcentaje del equity al inicio del día.
    Equity inicio de día = STARTING_CAPITAL_USDT + PnL realizado acumulado hasta AYER.
    Si hoy vas en ganancia, retorna un valor >= 0 (no dispara breaker).
    Si hay pérdida, retorna negativa (p.ej. -2.35).

    NOTA: Esta función requiere que la tabla trades tenga las columnas pnl_usd y closed_at.
    Por ahora, retorna 0.0 hasta que se actualice el schema de la base de datos.
    """
    starting_capital = _env_float("STARTING_CAPITAL_USDT", 500.0)
    today = _today_str_local()

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # Verificar si las columnas necesarias existen
        cur.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cur.fetchall()]

        if "pnl_usd" not in columns or "closed_at" not in columns:
            # Si no existen las columnas, retornar 0 (no cortar por breaker)
            print(
                f"⚠️ Columnas pnl_usd o closed_at no existen en trades. Columnas disponibles: {columns}"
            )
            return 0.0

        # PnL realizado hasta ayer (equity de apertura)
        cur.execute(
            """
            SELECT COALESCE(SUM(pnl_usd), 0.0) AS pnl_until_yesterday
            FROM trades
            WHERE closed_at IS NOT NULL
              AND date(closed_at) < ?
        """,
            (today,),
        )
        pnl_until_yesterday = cur.fetchone()[0] or 0.0

        equity_start_of_day = starting_capital + pnl_until_yesterday
        if equity_start_of_day <= 0:
            # Evita divisiones por cero o bases inválidas
            print("⚠️ Equity de inicio de día <= 0; devolviendo 0 para today_loss_pct()")
            return 0.0

        # PnL realizado de HOY
        cur.execute(
            """
            SELECT COALESCE(SUM(pnl_usd), 0.0) AS pnl_today
            FROM trades
            WHERE closed_at IS NOT NULL
              AND date(closed_at) = ?
        """,
            (today,),
        )
        pnl_today = cur.fetchone()[0] or 0.0

        # Si es pérdida, negativa; si es ganancia, positiva.
        loss_pct = (pnl_today / equity_start_of_day) * 100.0
        return float(loss_pct)
    except Exception:
        print("❌ Error calculando today_loss_pct")
        # Falla segura: no cortar por breaker si no podemos medir
        return 0.0
    finally:
        try:
            con.close()
        except Exception:
            pass


def load_settings():
    with open("config/settings.yaml", "r") as f:
        return yaml.safe_load(f)


def validate_order_parameters(
    symbol: str, side: str, quantity: float, price: float
) -> tuple[bool, str, float]:
    """
    Valida parámetros de orden antes de enviar a Binance
    Returns: (is_valid, message, adjusted_quantity)
    """
    try:
        # Validación básica de notional
        notional = quantity * price
        if notional < 10.0:
            # Ajustar cantidad para cumplir notional mínimo
            adjusted_quantity = (10.0 / price) * 1.001  # +0.1% margen
            adjusted_quantity = round(adjusted_quantity, 8)
            return (
                True,
                f"Quantity ajustada para cumplir notional mínimo: {adjusted_quantity}",
                adjusted_quantity,
            )

        return True, "Validación exitosa", quantity

    except Exception:
        return False, "Error de validación", 0.0


def main():
    load_dotenv()
    logger = setup_logging()
    cfg = load_settings()

    # KILL SWITCH - Parar bot si está activado
    kill_switch = os.getenv("KILL_SWITCH", "0")
    if kill_switch == "1":
        logger.critical("🚨 KILL SWITCH ACTIVADO - Bot detenido por seguridad")
        return

    # Determine bot mode from environment
    bot_mode = os.getenv("BOT_MODE", "mainnet")
    simulation_mode = bot_mode == "testnet" or bot_mode == "simulation"

    if simulation_mode:
        logger.info("EventArb Bot — Semana 5 (TESTNET/SIMULATION MODE)")
    else:
        logger.info("EventArb Bot — Semana 5 (MAINNET MODE)")

    # Initialize components
    init_db()
    risk_manager = RiskManager()
    order_router = OrderRouter(simulation=simulation_mode)
    sl_tp_manager = SLTPManager()
    oco_metrics = OCOMetrics()
    daily_limits = DailyLimits()

    paper_balance = Decimal("300.0")

    # Update daily limits from database
    daily_limits.update_from_database()

    # Circuit breaker with today_loss_pct
    DAILY_MAX_LOSS_PCT = _env_float("DAILY_MAX_LOSS_PCT", 5.0)

    # Check kill switch
    if os.getenv("KILL_SWITCH", "0") == "1":
        logger.warning("KILL_SWITCH=1 → parada inmediata del ciclo principal.")
        return

    # Check daily loss limit
    loss_pct = today_loss_pct(os.getenv("DB_PATH", "trades.db"))
    if loss_pct <= -DAILY_MAX_LOSS_PCT:
        logger.warning(
            f"Circuit breaker activado: pérdida diaria {loss_pct:.2f}% ≤ -{DAILY_MAX_LOSS_PCT:.2f}%. "
            "Activando KILL_SWITCH y saliendo."
        )
        os.environ["KILL_SWITCH"] = "1"
        return

    # Check daily limits
    if not daily_limits.can_trade():
        logger.warning("Trading halted due to daily limits")
        return

    # TODO: Event Scheduler ahora maneja los eventos automáticamente
    # Los eventos se disparan vía on_event() cuando llega su tiempo
    # events = read_events_from_sheet()
    # if not events:
    #     logger.warning("No se encontraron eventos habilitados en Sheet.")
    #     return

    logger.info("✅ Event Scheduler activo - esperando eventos programados...")
    return  # Salir temprano ya que los eventos se manejan vía scheduler

    # Código comentado - ahora manejado por Event Scheduler
    # for ev in events:
    #     actions = plan_actions_for_event(ev, cfg.get("default_notional_usd", 50.0))
    #     logger.info(
    #         f"📅 Evento: {ev.id} ({ev.kind}) @ {ev.t0_iso} symbols={ev.symbols}"
    #     )
    #     # ... resto del código comentado ...

    # Log OCO metrics summary (simulado para mantener compatibilidad)
    logger.info("📊 Event Scheduler: No hay métricas OCO en este modo")
    logger.info("📊 Daily stats: Trades: 0/20, PnL: 0.00% (modo scheduler)")


def on_event(event_data):
    """
    Handle scheduled events from Event Scheduler
    event_data: dict with id, t0_iso, symbol, type, consensus
    """
    try:
        print(f"🎯 Event received: {event_data}")

        # VERIFICAR EMERGENCY_STOP ANTES DE PROCESAR
        if check_emergency_stop():
            print("🚨 EMERGENCY_STOP ACTIVADO - Evento ignorado por seguridad")
            return

        # Extraer datos del evento
        event_id = event_data.get("id", "unknown")
        symbol = event_data.get("symbol", "UNKNOWN")
        event_type = event_data.get("type", "UNKNOWN")
        consensus = event_data.get("consensus", "{}")

        print(f"📅 Processing event: {event_id} ({symbol} {event_type})")

        # IMPLEMENTACIÓN DE ESTRATEGIAS DE TRADING
        if event_type == "CPI":
            print(f"🎯 CPI: Long USD si consensus > actual - {event_data}")
            # Estrategia inflación: Long USD si consensus > actual
            # TODO: Implementar lógica de trading real

        elif event_type == "FOMC":
            print(f"🎯 FOMC: Volatility play - {event_data}")
            # Estrategia Fed: Volatility play
            # TODO: Implementar lógica de trading real

        elif event_type == "EARNINGS":
            print(f"🎯 EARNINGS: Momentum trading - {event_data}")
            # Estrategia earnings: Momentum trading
            # TODO: Implementar lógica de trading real

        elif event_type == "TEST":
            print(f"🧪 Test Event for {symbol} - Evento de prueba exitoso")
            # Evento de prueba, no hacer nada especial

        else:
            print(f"❓ Unknown event type: {event_type} for {symbol}")

        # Log del evento procesado
        print(f"✅ Event {event_id} processed successfully")

    except Exception:
        print(f"❌ Error handling event: error")
        print(f"Event data: {event_data}")


if __name__ == "__main__":
    try:
        main()
        print("✅ Main function completed successfully")
    except Exception:
        print(f"❌ Error in main: error")

    # Mantener el proceso vivo para que el Event Scheduler funcione
    print("🔄 Manteniendo app.py ejecutándose para Event Scheduler...")
    import time

    while True:
        try:
            time.sleep(60)  # Sleep para no consumir CPU
            print("💓 Heartbeat: app.py sigue ejecutándose...")
        except KeyboardInterrupt:
            print("📴 Interrupción recibida, cerrando app.py...")
            break
        except Exception:
            print(f"❌ Error en loop principal: error")
            time.sleep(10)  # Pausa más corta en caso de error
