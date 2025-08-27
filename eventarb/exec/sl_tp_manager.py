import logging
from decimal import Decimal

logger = logging.getLogger("eventarb")


class SLTPManager:
    def __init__(self, tick_size: Decimal = Decimal("0.01")):
        self.tick_size = tick_size
        self.retry_count = 0
        self.max_retries = 1

    def ensure_relation(
        self, entry_price: Decimal, sl_pct: float, tp_pct: float
    ) -> tuple:
        """Ensure valid SL/TP relation with nudge if needed"""
        if entry_price <= Decimal("0"):
            return entry_price, entry_price

        # Calculate initial SL/TP prices
        if sl_pct > 0 and tp_pct > 0:
            sl_price = entry_price * (1 - Decimal(sl_pct) / 100)
            tp_price = entry_price * (1 + Decimal(tp_pct) / 100)
        else:
            return entry_price, entry_price

        # Check if SL and TP are valid (SL < entry < TP for BUY, opposite for SELL)
        is_valid = sl_price < entry_price < tp_price

        if not is_valid and self.retry_count < self.max_retries:
            logger.warning(
                f"Invalid SL/TP relation - nudging prices (attempt {self.retry_count + 1})"
            )
            self.retry_count += 1

            # Nudge prices by tick size
            if sl_price >= entry_price:
                sl_price -= self.tick_size
            if tp_price <= entry_price:
                tp_price += self.tick_size

            # Recursive check
            return self.ensure_relation(entry_price, sl_pct, tp_pct)

        if not is_valid:
            logger.error("Failed to establish valid SL/TP relation after retries")
            return entry_price, entry_price

        logger.info(
            f"✅ SL/TP relation validated: SL={sl_price:.2f}, TP={tp_price:.2f}"
        )
        return sl_price, tp_price

    def reset_retries(self):
        """Reset retry counter"""
        self.retry_count = 0
