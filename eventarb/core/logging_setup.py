import logging
import os


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Avoid reconfiguring if already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=getattr(logging, level, logging.INFO),
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
    
    return logging.getLogger("eventarb")
