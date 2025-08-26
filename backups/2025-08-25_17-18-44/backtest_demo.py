#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import logging
import pandas as pd
from decimal import Decimal
from eventarb.core.logging_setup import setup_logging
from eventarb.core.models import Event, PlannedAction
from eventarb.backtest.engine import load_price_data, run_backtest
from eventarb.backtest.metrics import summarize_backtest

def main():
    logger = setup_logging()
    logger.info("Running backtest demo...")
    
    # Load sample price data
    price_data = load_price_data("eventarb/backtest/sample_data/BTCUSDT_1m.csv")
    if price_data.empty:
        logger.error("No price data loaded")
        return
    
    # Create sample actions for backtest
    sample_actions = [
        PlannedAction(
            event_id="test_1",
            symbol="BTCUSDT",
            side="BUY",
            notional_usd=Decimal("1000"),
            tp_pct=3.0,
            sl_pct=1.5,
            timing="AT_T0"
        ),
        PlannedAction(
            event_id="test_2", 
            symbol="BTCUSDT",
            side="SELL",
            notional_usd=Decimal("800"),
            tp_pct=2.5,
            sl_pct=1.2,
            timing="AT_T0"
        )
    ]
    
    # Run backtest
    trades = run_backtest(sample_actions, price_data)
    
    # Print results
    logger.info(f"Backtest completed: {len(trades)} trades")
    
    for i, trade in enumerate(trades, 1):
        status = "WIN" if trade['win'] else "LOSS"
        logger.info(f"Trade {i}: {trade['symbol']} {trade['side']} "
                   f"Entry: {trade['entry_price']:.2f} Exit: {trade['exit_price']:.2f} "
                   f"PnL: {trade['pnl_pct']:.2f}% ({status})")
    
    # Show summary metrics
    metrics = summarize_backtest(trades)
    if metrics:
        logger.info("Backtest Summary:")
        logger.info(f"Trades: {metrics['n_trades']}")
        logger.info(f"Win Rate: {metrics['win_rate']:.2%}")
        logger.info(f"Avg Return: {metrics['avg_return']:.2f}%")
        logger.info(f"Profit Factor: {metrics['profit_factor']:.2f}")
        logger.info(f"Total Return: {metrics['total_return']:.2f}%")

if __name__ == "__main__":
    main()

