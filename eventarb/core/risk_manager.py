import os
import sqlite3
import datetime
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.db_path = os.getenv("DB_PATH", "trades.db")
    
    def today_trades_count(self) -> int:
        """Count trades executed today"""
        today = datetime.date.today().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM trades WHERE date(created_at) = ?", 
                    (today,)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting today's trades: {e}")
            return 0
    
    def under_daily_trade_limit(self) -> bool:
        """Check if we're under the daily trade limit"""
        limit = int(os.getenv("DAILY_MAX_TRADES", "20"))
        count = self.today_trades_count()
        
        if count >= limit:
            logger.warning(
                f"⛔ DAILY_MAX_TRADES alcanzado ({count}/{limit}). "
                "No se abrirán más operaciones hoy."
            )
            return False
        
        logger.info(f"📊 Trades hoy: {count}/{limit}")
        return True
    
    def notional_for_balance(self, balance: Decimal) -> Decimal:
        """Calculate safe notional based on balance and risk limits"""
        # Risk per trade: 1% of balance
        risk_pct = Decimal("0.01")
        return balance * risk_pct
    
    def release_position(self):
        """Release position for next trade"""
        # This method can be extended for position management
        pass

