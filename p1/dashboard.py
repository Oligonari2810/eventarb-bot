from __future__ import annotations

from fastapi import FastAPI

from p1.daily_counter import get_daily_count, calculate_daily_pnl

app = FastAPI(title="EventArb Monitoring")


def get_bot_state() -> str:
    # TODO: enlazar con runner/health.json si existe
    return "RUNNING"


def get_last_trade_time() -> str:
    return ""


def get_uptime() -> str:
    return ""


@app.get("/metrics")
async def metrics():
    return {
        "trades_today": get_daily_count(),
        "win_rate": "0.0",  # TODO
        "pnl_day": calculate_daily_pnl(),
        "state": get_bot_state(),
        "last_trade_ts": get_last_trade_time(),
        "uptime": get_uptime(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
