from __future__ import annotations

import os
import sys
from fastapi import FastAPI

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-08-26T12:43:00Z"}


if __name__ == "__main__":
    import uvicorn

    # Configuración flexible del puerto
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Iniciando EventArb Dashboard en {host}:{port}")

    try:
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        print(f"❌ Error iniciando dashboard: {e}")
        sys.exit(1)
