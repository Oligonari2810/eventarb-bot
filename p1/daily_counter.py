from __future__ import annotations

import sqlite3
from datetime import date, datetime
from decimal import Decimal

LIMIT_PER_DAY = 20


def _today() -> date:
    return datetime.now().date()


def get_daily_count(db_path: str = "trades.db", limit: int = LIMIT_PER_DAY) -> str:
    try:
        with sqlite3.connect(db_path) as conn:
            # Usar la nueva tabla bot_state para conteo persistente
            cur = conn.execute(
                """
                SELECT trades_done FROM bot_state WHERE date = date('now')
            """
            )
            result = cur.fetchone()

            if result:
                count = result[0] or 0
            else:
                # Fallback: contar desde trades table
                cur = conn.execute(
                    """
                    SELECT COUNT(*) FROM trades
                    WHERE DATE(created_at) = DATE('now')
                """
                )
                count = cur.fetchone()[0] or 0

                # Inicializar bot_state si no existe
                conn.execute(
                    """
                    INSERT OR IGNORE INTO bot_state (date, trades_done, loss_cents, emergency_stop)
                    VALUES (date('now'), ?, 0, 0)
                """,
                    (count,),
                )
                conn.commit()

            return f"{count}/{limit}"
    except Exception:
        # Si no existe DB/tabla/columnas, retornar conteo seguro
        return f"0/{limit}"


def calculate_daily_pnl(db_path: str = "trades.db") -> Decimal:
    """Calcula el PnL diario desde la tabla trades"""
    try:
        with sqlite3.connect(db_path) as conn:
            # Usar la nueva tabla bot_state para PnL persistente (si existe)
            try:
                cur = conn.execute(
                    """
                    SELECT loss_cents FROM bot_state WHERE date = date('now')
                    """
                )
                result = cur.fetchone()

                if result:
                    loss_cents = result[0] or 0
                    return Decimal(loss_cents) / 100
            except Exception:
                # Tabla bot_state no existe, continuar con fallback
                pass

            # Fallback: intentar con estructura de test (pnl_usd directo)
            try:
                cur = conn.execute(
                    """
                    SELECT COALESCE(SUM(pnl_usd), 0) as daily_pnl
                    FROM trades 
                    WHERE DATE(open_time) = DATE('now')
                    """
                )
                daily_pnl = cur.fetchone()[0] or 0
                return Decimal(str(daily_pnl))
            except Exception:
                # Fallback: intentar con la estructura real de trades (precios)
                try:
                    cur = conn.execute(
                        """
                        SELECT 
                            COALESCE(SUM(
                                CASE 
                                    WHEN tp_price_cents IS NOT NULL THEN 
                                        (tp_price_cents - entry_price_cents) * quantity_cents / 10000
                                    WHEN sl_price_cents IS NOT NULL THEN 
                                        (sl_price_cents - entry_price_cents) * quantity_cents / 10000
                                    ELSE 0
                                END
                            ), 0) as daily_pnl_cents
                        FROM trades 
                        WHERE DATE(created_at) = DATE('now')
                        """
                    )
                    pnl_cents = cur.fetchone()[0] or 0
                    return Decimal(pnl_cents) / 100
                except Exception:
                    return Decimal("0.0")

    except Exception:
        return Decimal("0.0")


def increment_daily_count(db_path: str = "trades.db") -> bool:
    """Incrementa el contador diario de trades"""
    try:
        with sqlite3.connect(db_path) as conn:
            # USAR UTC para consistencia con get_bot_state
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Incrementar trades_done
            conn.execute(
                """
                UPDATE bot_state SET trades_done = trades_done + 1, last_updated = datetime('now')
                WHERE date = ?
            """,
                (today,),
            )

            # Si no se actualizó ninguna fila, crear nueva entrada
            if conn.total_changes == 0:
                conn.execute(
                    """
                    INSERT INTO bot_state (date, trades_done, loss_cents, emergency_stop)
                    VALUES (?, 1, 0, 0)
                """,
                    (today,),
                )

            conn.commit()
            return True

    except Exception:
        return False


def update_daily_loss(loss_cents: int, db_path: str = "trades.db") -> bool:
    """Actualiza la pérdida diaria en centavos"""
    try:
        with sqlite3.connect(db_path) as conn:
            # USAR UTC para consistencia con get_bot_state
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Actualizar loss_cents
            conn.execute(
                """
                UPDATE bot_state SET loss_cents = ?, last_updated = datetime('now')
                WHERE date = ?
            """,
                (loss_cents, today),
            )

            # Si no se actualizó ninguna fila, crear nueva entrada
            if conn.total_changes == 0:
                conn.execute(
                    """
                    INSERT INTO bot_state (date, trades_done, loss_cents, emergency_stop)
                    VALUES (?, 0, ?, 0)
                """,
                    (today, loss_cents),
                )

            conn.commit()
            return True

    except Exception:
        return False


def get_bot_state(db_path: str = "trades.db") -> dict:
    """Obtiene el estado completo del bot para hoy"""
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute(
                """
                SELECT trades_done, loss_cents, max_trades_per_day, daily_loss_limit_cents, emergency_stop
                FROM bot_state WHERE date = date('now')
            """
            )
            result = cur.fetchone()

            if result:
                return {
                    "trades_done": result[0] or 0,
                    "loss_cents": result[1] or 0,
                    "max_trades_per_day": result[2] or LIMIT_PER_DAY,
                    "daily_loss_limit_cents": result[3] or 10000,  # $100.00 default
                    "emergency_stop": bool(result[4]),
                }
            else:
                # Retornar valores por defecto
                return {
                    "trades_done": 0,
                    "loss_cents": 0,
                    "max_trades_per_day": LIMIT_PER_DAY,
                    "daily_loss_limit_cents": 10000,
                    "emergency_stop": False,
                }

    except Exception:
        return {
            "trades_done": 0,
            "loss_cents": 0,
            "max_trades_per_day": LIMIT_PER_DAY,
            "daily_loss_limit_cents": 10000,
            "emergency_stop": False,
        }
