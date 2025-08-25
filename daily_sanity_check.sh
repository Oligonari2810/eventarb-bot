#!/usr/bin/env bash
set -euo pipefail

cd /Users/anamarperezmarrero/eventarb-bot/eventarb-bot
source .venv/bin/activate
export $(grep -v '^#' .env.production | xargs)

echo "== Sanity $(date) =="

# 1) Binance + reloj servidor
python - <<'PY'
import os, sys
from binance.client import Client
try:
    c = Client(api_key=os.environ["BINANCE_API_KEY"], api_secret=os.environ["BINANCE_API_SECRET"])
    c.ping()
    server_time = c.get_server_time()
    print("Binance OK — server time:", server_time)
except Exception as e:
    print("Binance FAIL:", e)
    sys.exit(1)
PY

# 2) Pérdida diaria (para breaker)
python - <<'PY'
from app import today_loss_pct
print("today_loss_pct:", today_loss_pct())
PY

# 3) DB viva
sqlite3 trades.db "SELECT date('now'), COUNT(*) FROM trades;"
echo "Sanity OK"
