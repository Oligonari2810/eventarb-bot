#!/usr/bin/env python3
"""
EventArb Bot - Aplicación principal
Bot para automatizar eventos y notificaciones
"""

import os
import sqlite3
from datetime import datetime
from decimal import Decimal

import yaml
from dotenv import load_dotenv

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
        self.daily_max_loss_pct = float(os.getenv("DAILY_MAX_LOSS_PCT", "5.0"))
        self.daily_max_trades = int(os.getenv("DAILY_MAX_TRADES", "20"))
        self.today_trades = 0
        self.today_pnl = 0.0

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

        except Exception as e:
            print(f"Error calculating today_loss_pct: {e}")
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

        except Exception as e:
            print(f"Error updating from database: {e}")


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
    except Exception as e:
        print(f"❌ Error calculando today_loss_pct: {e}")
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


def main():
    load_dotenv()
    logger = setup_logging()
    cfg = load_settings()

    # KILL SWITCH - Parar bot si está activado
    kill_switch = os.getenv("KILL_SWITCH", "0")
    if kill_switch == "1":
        logger.critical("🚨 KILL SWITCH ACTIVADO - Bot detenido por seguridad")
        return

    logger.info("EventArb Bot — Semana 5 (MAINNET MODE)")

    # Initialize components
    init_db()
    risk_manager = RiskManager()
    order_router = OrderRouter(simulation=cfg.get("simulation", True))
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

    events = read_events_from_sheet()
    if not events:
        logger.warning("No se encontraron eventos habilitados en Sheet.")
        return

    for ev in events:
        actions = plan_actions_for_event(ev, cfg.get("default_notional_usd", 50.0))
        logger.info(
            f"📅 Evento: {ev.id} ({ev.kind}) @ {ev.t0_iso} symbols={ev.symbols}"
        )

        for a in actions:
            if not daily_limits.can_trade():
                break

            # Check daily trade limit
            if not risk_manager.under_daily_trade_limit():
                logger.warning(f"⛔ Saltando {a.symbol} - límite diario alcanzado")
                break

            risk_notional = risk_manager.notional_for_balance(paper_balance)
            if risk_notional <= Decimal("0"):
                continue

            a.notional_usd = risk_notional

            logger.info(
                f"🧠 Plan: {a.symbol} {a.side} notional=${a.notional_usd} TP={a.tp_pct}% SL={a.sl_pct}% timing={a.timing}"
            )

            if a.side != "FLAT":
                last_price = (
                    Decimal("50000.0") if "BTC" in a.symbol else Decimal("3000.0")
                )

                # Ensure valid SL/TP relation
                sl_price, tp_price = sl_tp_manager.ensure_relation(
                    last_price, a.sl_pct, a.tp_pct
                )

                fill = order_router.place_market_real(
                    a.symbol, a.side, a.notional_usd, last_price
                )

                # Record OCO metrics
                if sl_price != last_price and tp_price != last_price:
                    oco_metrics.record_success(a.symbol)
                    logger.info(
                        f"📊 OCO: SL={sl_price:.2f} TP={tp_price:.2f} (relation valid)"
                    )
                else:
                    oco_metrics.record_failure(a.symbol, "invalid_relation")

                # Insert to database
                insert_trade(
                    event_id=ev.id,
                    symbol=a.symbol,
                    side=a.side,
                    quantity=Decimal(fill["quantity"]),
                    entry_price=last_price,
                    tp_price=tp_price,
                    sl_price=sl_price,
                    notional_usd=a.notional_usd,
                    simulated=fill["simulated"],
                )

                # Log to Google Sheets
                trade_data = {
                    "event_id": ev.id,
                    "symbol": a.symbol,
                    "side": a.side,
                    "quantity": float(fill["quantity"]),
                    "entry_price": float(last_price),
                    "tp_price": float(tp_price),
                    "sl_price": float(sl_price),
                    "notional_usd": float(a.notional_usd),
                    "simulated": fill["simulated"],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "pnl_pct": 0.0,  # Estimated PnL
                }
                sheets_logger.log_trade(trade_data)

                # Update daily limits
                daily_limits.record_trade(estimated_pnl=0.0)

                risk_manager.release_position()
                sl_tp_manager.reset_retries()

        if os.getenv("SEND_TELEGRAM_ON_PLAN") == "1":
            send_telegram(
                f"[Plan Semana5] {ev.id} {ev.kind} -> {len(actions)} acción(es)"
            )

    # Log OCO metrics summary
    oco_metrics.log_summary()
    logger.info(
        f"Daily stats: Trades: {daily_limits.today_trades}, PnL: {daily_limits.today_pnl:.2f}%"
    )


if __name__ == "__main__":
    main()
