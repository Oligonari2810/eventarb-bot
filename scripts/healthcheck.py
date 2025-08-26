#!/usr/bin/env python3

import logging
import os
import time
from datetime import datetime

from eventarb.notify.telegram_stub import send_telegram

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/healthcheck.log"), logging.StreamHandler()],
)

logger = logging.getLogger("eventarb-healthcheck")


def health_check():
    """Perform health check and log status"""
    try:
        # Basic system check
        import psutil

        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        status_message = (
            f"✅ HealthCheck - {datetime.utcnow().isoformat()}Z\n"
            f"CPU: {cpu_percent}% | Memory: {memory.percent}%\n"
            f"Available: {memory.available // (1024**2)}MB"
        )

        logger.info(status_message)

        # Telegram notification if enabled
        if os.getenv("SEND_TELEGRAM_ON_PLAN") == "1":
            send_telegram(status_message)

        return True

    except ImportError:
        # Fallback without psutil
        status_message = f"✅ HealthCheck - {datetime.utcnow().isoformat()}Z"
        logger.info(status_message)

        if os.getenv("SEND_TELEGRAM_ON_PLAN") == "1":
            send_telegram(status_message)

        return True
    except Exception as e:
        error_message = f"❌ HealthCheck Failed: {e}"
        logger.error(error_message)
        return False


def main():
    """Main healthcheck loop"""
    logger.info("Starting EventArb HealthCheck Service")

    while True:
        try:
            health_check()

            # Wait for next check
            sleep_minutes = int(os.getenv("HEALTHCHECK_MINUTES", "10"))
            time.sleep(sleep_minutes * 60)

        except KeyboardInterrupt:
            logger.info("HealthCheck service stopped by user")
            break
        except Exception as e:
            logger.error(f"HealthCheck loop error: {e}")
            time.sleep(60)  # Wait before retry


if __name__ == "__main__":
    main()
