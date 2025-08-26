import os
import sqlite3
import tempfile
from datetime import datetime

import sys

sys.path.append("p1")
from daily_counter import calculate_daily_pnl, get_daily_count


def test_daily_counter_with_db():
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "trading.db")
        with sqlite3.connect(db) as conn:
            conn.execute(
                "CREATE TABLE trades (open_time TEXT, close_time TEXT, pnl_usd REAL)"
            )
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO trades VALUES (?,?,?)", (now, now, 5.0))
            conn.execute("INSERT INTO trades VALUES (?,?,?)", (now, now, -1.5))
            conn.commit()
        assert get_daily_count(db_path=db).endswith("/20")
        assert calculate_daily_pnl(db_path=db) == 3.5
