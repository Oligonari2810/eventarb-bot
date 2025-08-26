import logging
import os
from typing import Any, Dict

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("eventarb")


class GoogleSheetsLogger:
    def __init__(self):
        self.credentials_b64 = os.getenv("GOOGLE_SHEETS_CREDENTIALS_B64")
        self.sheet_id = os.getenv("TRADES_SHEET_ID")
        self.sheet_range = os.getenv("TRADES_SHEET_RANGE", "A2:K2000")
        self.service = None

        if self.credentials_b64 and self.sheet_id:
            self._initialize_service()

    def _initialize_service(self):
        """Initialize Google Sheets service"""
        try:
            import base64
            import json

            creds_json = base64.b64decode(self.credentials_b64).decode("utf-8")
            creds = Credentials.from_service_account_info(
                json.loads(creds_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            self.service = build("sheets", "v4", credentials=creds)
            logger.info("✅ Google Sheets logger initialized")
        except Exception as e:
            logger.warning(f"Google Sheets initialization failed: {e}")
            self.service = None

    def log_trade(self, trade_data: Dict[str, Any]):
        """Log trade to Google Sheets"""
        if not self.service or not self.sheet_id:
            logger.warning("Google Sheets logging skipped - no credentials")
            return False

        try:
            # Prepare trade data for sheets
            values = [
                [
                    trade_data.get("event_id", ""),
                    trade_data.get("symbol", ""),
                    trade_data.get("side", ""),
                    trade_data.get("quantity", 0),
                    trade_data.get("entry_price", 0),
                    trade_data.get("tp_price", 0),
                    trade_data.get("sl_price", 0),
                    trade_data.get("notional_usd", 0),
                    trade_data.get("simulated", True),
                    trade_data.get("timestamp", ""),
                    trade_data.get("pnl_pct", 0),
                ]
            ]

            body = {"values": values}
            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.sheet_id,
                    range=self.sheet_range,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

            logger.info(f"✅ Trade logged to Google Sheets: {trade_data['symbol']}")
            return True

        except HttpError as e:
            logger.error(f"Google Sheets API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Google Sheets logging failed: {e}")
            return False


# Global instance
sheets_logger = GoogleSheetsLogger()
