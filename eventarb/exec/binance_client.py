import logging
import os

from binance.client import Client
from binance.enums import *

logger = logging.getLogger("eventarb")


def build_binance_client():
    """Build Binance client for testnet"""
    testnet = os.getenv("BINANCE_TESTNET", "0") == "1"
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        logger.warning("Binance credentials not set - using dummy client")
        return None

    if testnet:
        client = Client(api_key, api_secret, testnet=True)
        logger.info("✅ Binance Testnet client configured")
    else:
        client = Client(api_key, api_secret)
        logger.info("✅ Binance Mainnet client configured")

    # Test connection
    try:
        client.ping()
        logger.info("✅ Binance connection successful")
        return client
    except Exception as e:
        logger.error(f"❌ Binance connection failed: {e}")
        return None
