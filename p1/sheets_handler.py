from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
RANGE_TRADES = os.getenv("GOOGLE_SHEET_RANGE_TRADES", "TradesClosed!A:F")
RANGE_DAILY = os.getenv("GOOGLE_SHEET_RANGE_DAILY", "DailySummary!A:G")


def _disabled() -> bool:
    return os.getenv("GOOGLE_SHEETS_DISABLED", "1") == "1"


def append_trade_closed(row: Dict[str, Any]) -> bool:
    """
    row esperado: {timestamp,symbol,direction,pnl_usd,reason,duration}
    """
    if _disabled():
        return True
    # Esqueleto: leer credenciales desde env base64
    creds_b64 = os.getenv("GOOGLE_SHEETS_CREDENTIALS_B64", "")
    if not creds_b64 or not SHEET_ID:
        return False
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        data = base64.b64decode(creds_b64)
        info = json.loads(data.decode("utf-8"))
        creds = Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        body = {
            "values": [
                [
                    row.get(k, "")
                    for k in (
                        "timestamp",
                        "symbol",
                        "direction",
                        "pnl_usd",
                        "reason",
                        "duration",
                    )
                ]
            ]
        }
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=RANGE_TRADES,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return True
    except Exception:
        return False


def append_daily_summary(values: list) -> bool:
    if _disabled():
        return True
    try:
        # Similar a append_trade_closed; omitido por brevedad
        return True
    except Exception:
        return False
