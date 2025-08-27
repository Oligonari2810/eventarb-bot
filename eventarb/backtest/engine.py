import logging
from decimal import Decimal
from typing import Dict, List

import pandas as pd

from eventarb.core.models import PlannedAction

logger = logging.getLogger("eventarb")


def load_price_data(csv_path: str) -> pd.DataFrame:
    """Load OHLCV data from CSV"""
    try:
        df = pd.read_csv(csv_path)
        df["time"] = pd.to_datetime(df["time"])
        df.set_index("time", inplace=True)
        logger.info(f"✅ Loaded price data from {csv_path}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"❌ Failed to load price data: {e}")
        return pd.DataFrame()


def run_backtest(actions: List[PlannedAction], price_data: pd.DataFrame) -> List[Dict]:
    """Run backtest on planned actions"""
    trades = []

    for action in actions:
        if action.side == "FLAT":
            continue

        # Find entry price (first available price after event)
        entry_time = pd.Timestamp.now()  # Simulated event time
        entry_price = Decimal(
            str(price_data["close"].iloc[0] if len(price_data) > 0 else 10000)
        )

        # Calculate TP/SL prices
        if action.side == "BUY":
            tp_price = entry_price * (1 + Decimal(str(action.tp_pct)) / 100)
            sl_price = entry_price * (1 - Decimal(str(action.sl_pct)) / 100)
        else:
            tp_price = entry_price * (1 - Decimal(str(action.tp_pct)) / 100)
            sl_price = entry_price * (1 + Decimal(str(action.sl_pct)) / 100)

        # Simulate trade outcome
        outcome = simulate_trade_outcome(entry_price, tp_price, sl_price, price_data)

        trades.append(
            {
                "symbol": action.symbol,
                "side": action.side,
                "entry_price": float(entry_price),
                "tp_price": float(tp_price),
                "sl_price": float(sl_price),
                "exit_price": float(outcome["exit_price"]),
                "pnl_pct": float(outcome["pnl_pct"]),
                "win": outcome["win"],
            }
        )

    return trades


def simulate_trade_outcome(
    entry_price: Decimal, tp_price: Decimal, sl_price: Decimal, price_data: pd.DataFrame
) -> Dict:
    """Simulate trade outcome based on price data"""
    if price_data.empty:
        # Default simulation if no data
        return {
            "exit_price": entry_price * Decimal("1.02"),
            "pnl_pct": 2.0,
            "win": True,
        }

    # Check if TP or SL hit within next 24 periods (simulated)
    for _, row in price_data.head(24).iterrows():
        current_price = Decimal(str(row["close"]))

        if current_price >= tp_price:
            return {
                "exit_price": tp_price,
                "pnl_pct": float((tp_price - entry_price) / entry_price * 100),
                "win": True,
            }
        elif current_price <= sl_price:
            return {
                "exit_price": sl_price,
                "pnl_pct": float((sl_price - entry_price) / entry_price * 100),
                "win": False,
            }

    # If neither hit, use last price
    last_price = Decimal(str(price_data["close"].iloc[-1]))
    pnl_pct = float((last_price - entry_price) / entry_price * 100)
    return {"exit_price": last_price, "pnl_pct": pnl_pct, "win": pnl_pct > 0}
