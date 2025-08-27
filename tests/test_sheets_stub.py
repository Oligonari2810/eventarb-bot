import sys

sys.path.append("p1")
from sheets_handler import append_trade_closed


def test_sheets_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_DISABLED", "1")
    ok = append_trade_closed(
        {
            "timestamp": "2025-01-01 00:00:00",
            "symbol": "BTC/USDT",
            "direction": "long",
            "pnl_usd": 1.23,
            "reason": "TP",
            "duration": "00:05:00",
        }
    )
    assert ok is True
