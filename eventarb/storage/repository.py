import sqlite3
import os
import logging
from decimal import Decimal

logger = logging.getLogger("eventarb")

def init_db():
    """Initialize SQLite database with trades table"""
    db_path = os.getenv("DB_PATH", "trades.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        tp_price REAL,
        sl_price REAL,
        notional_usd REAL NOT NULL,
        simulated BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Enable WAL for better concurrency
    cursor.execute("PRAGMA journal_mode=WAL")
    
    conn.commit()
    conn.close()
    logger.info(f"✅ Database initialized at {db_path}")

def insert_trade(event_id: str, symbol: str, side: str, quantity: Decimal, 
                entry_price: Decimal, tp_price: Decimal, sl_price: Decimal, 
                notional_usd: Decimal, simulated: bool = True):
    """Insert trade into database"""
    db_path = os.getenv("DB_PATH", "trades.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO trades (event_id, symbol, side, quantity, entry_price, 
                       tp_price, sl_price, notional_usd, simulated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id, symbol, side, float(quantity), float(entry_price),
        float(tp_price) if tp_price else None,
        float(sl_price) if sl_price else None,
        float(notional_usd), simulated
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"✅ Trade recorded in database: {symbol} {side}")

