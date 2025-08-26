import logging
import os
from decimal import Decimal

logger = logging.getLogger("eventarb")


class RiskManager:
    def __init__(self):
        self.risk_per_trade_pct = Decimal(os.getenv("RISK_PER_TRADE_PCT", "1.5"))
        self.max_positions = int(os.getenv("MAX_CONCURRENT_POSITIONS", "3"))
        self.current_positions = 0

    def notional_for_balance(self, balance: Decimal) -> Decimal:
        """Calculate position size based on account balance and risk percentage"""
        if self.current_positions >= self.max_positions:
            logger.warning("Max concurrent positions reached - skipping trade")
            return Decimal("0")

        risk_amount = balance * (self.risk_per_trade_pct / Decimal("100"))
        self.current_positions += 1
        return risk_amount

    def release_position(self):
        """Release a position slot"""
        if self.current_positions > 0:
            self.current_positions -= 1
