import logging
from collections import defaultdict

logger = logging.getLogger("eventarb")


class OCOMetrics:
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.retry_count = 0
        self.fallback_count = 0
        self.symbol_stats = defaultdict(
            lambda: {"success": 0, "failure": 0, "retries": 0}
        )

    def record_success(self, symbol: str):
        """Record successful OCO order"""
        self.success_count += 1
        self.symbol_stats[symbol]["success"] += 1
        logger.debug(f"OCO success recorded for {symbol}")

    def record_failure(self, symbol: str, reason: str = "unknown"):
        """Record failed OCO order"""
        self.failure_count += 1
        self.symbol_stats[symbol]["failure"] += 1
        logger.warning(f"OCO failure for {symbol}: {reason}")

    def record_retry(self, symbol: str):
        """Record retry attempt"""
        self.retry_count += 1
        self.symbol_stats[symbol]["retries"] += 1

    def record_fallback(self, symbol: str):
        """Record fallback to manual orders"""
        self.fallback_count += 1
        logger.info(f"Fallback to manual orders for {symbol}")

    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0

    def get_summary(self) -> dict:
        """Get metrics summary"""
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "retry_count": self.retry_count,
            "fallback_count": self.fallback_count,
            "success_rate": self.get_success_rate(),
            "symbol_stats": dict(self.symbol_stats),
        }

    def log_summary(self):
        """Log metrics summary"""
        summary = self.get_summary()
        logger.info("OCO Metrics Summary:")
        logger.info(f"Success Rate: {summary['success_rate']:.2%}")
        logger.info(f"Total Success: {summary['success_count']}")
        logger.info(f"Total Failures: {summary['failure_count']}")
        logger.info(f"Total Retries: {summary['retry_count']}")
        logger.info(f"Total Fallbacks: {summary['fallback_count']}")
