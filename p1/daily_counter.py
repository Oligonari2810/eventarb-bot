from __future__ import annotations

import sqlite3
from datetime import date, datetime

LIMIT_PER_DAY = 20


def _today() -> date:
    return datetime.now().date()


def get_daily_count(db_path: str = "trading.db", limit: int = LIMIT_PER_DAY) -> str:
    try:
        with sqlite3.connect(db_path) as conn:
            # Intentar contar por fecha de open y close en hoy; si no hay columnas, cae al except
            cur = conn.execute(
                """
                SELECT COUNT(*) FROM trades
                WHERE DATE(open_time) = DATE('now') AND (close_time IS NULL OR DATE(close_time) = DATE('now'))
            """
            )
            count = cur.fetchone()[0] or 0
            return f"{count}/{limit}"
    except Exception:
        # Si no existe DB/tabla/columnas, retornar conteo seguro
        return f"0/{limit}"


def calculate_daily_pnl(db_path: str = "trading.db") -> float:
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute(
                """
                SELECT COALESCE(SUM(pnl_usd),0.0) FROM trades
                WHERE close_time IS NOT NULL AND DATE(close_time) = DATE('now')
            """
            )
            return float(cur.fetchone()[0] or 0.0)
    except Exception:
        return 0.0
