from typing import Dict, List

import numpy as np


def summarize_backtest(trades: List[Dict]) -> Dict:
    """Calculate backtest performance metrics"""
    if not trades:
        return {}

    wins = [t for t in trades if t["win"]]
    losses = [t for t in trades if not t["win"]]

    n_trades = len(trades)
    win_rate = len(wins) / n_trades if n_trades > 0 else 0

    # Calculate returns
    returns = [t["pnl_pct"] for t in trades]
    avg_return = np.mean(returns) if returns else 0
    std_return = np.std(returns) if returns else 0

    # Profit factor
    gross_profit = sum(max(t["pnl_pct"], 0) for t in trades)
    gross_loss = abs(sum(min(t["pnl_pct"], 0) for t in trades))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    return {
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_return": avg_return,
        "std_return": std_return,
        "profit_factor": profit_factor,
        "total_return": sum(returns),
        "best_trade": max(returns) if returns else 0,
        "worst_trade": min(returns) if returns else 0,
    }
