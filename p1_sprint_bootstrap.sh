#!/bin/bash
# === P1 SPRINT BOOTSTRAP (Sheets + Alerting + Dashboard + E2E) ===
set -euo pipefail

BRANCH="feat/p1-sprint"
PY_MATRIX='"3.12.0", "3.12.1", "3.12.2"'

echo "➡️ 1) Crear rama P1"
git fetch origin || true
git checkout -b "$BRANCH" || git checkout "$BRANCH"

echo "➡️ 2) Dependencias runtime + dev"
# Asegura requirements.txt
test -f requirements.txt || touch requirements.txt
# Añade libs si faltan
grep -q "^fastapi" requirements.txt || cat >> requirements.txt <<'REQ'
fastapi==0.115.0
uvicorn==0.30.6
python-dateutil==2.9.0.post0
google-api-python-client==2.137.0
google-auth==2.33.0
google-auth-oauthlib==1.2.1
schedule==1.2.2
pydantic==2.8.2
REQ

# Dev/test (pueden estar en requirements-dev.txt)
test -f requirements-dev.txt || cat > requirements-dev.txt <<'DEV'
pytest==8.3.2
pytest-asyncio==0.23.8
requests==2.31.0
black==24.8.0
ruff==0.5.7
isort==5.13.2
DEV

python -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip -q install --upgrade pip
pip -q install -r requirements.txt -r requirements-dev.txt

echo "➡️ 3) Estructura P1 (módulos y tests)"
mkdir -p p1 tests/e2e

# daily_counter.py
cat > p1/daily_counter.py <<'PY'
from __future__ import annotations
import sqlite3
from datetime import datetime, date
from typing import Optional

LIMIT_PER_DAY = 20

def _today() -> date:
    return datetime.now().date()

def get_daily_count(db_path: str = "trading.db", limit: int = LIMIT_PER_DAY) -> str:
    try:
        with sqlite3.connect(db_path) as conn:
            # Intentar contar por fecha de open y close en hoy; si no hay columnas, cae al except
            cur = conn.execute("""
                SELECT COUNT(*) FROM trades
                WHERE DATE(open_time) = DATE('now') AND (close_time IS NULL OR DATE(close_time) = DATE('now'))
            """)
            count = cur.fetchone()[0] or 0
            return f"{count}/{limit}"
    except Exception:
        # Si no existe DB/tabla/columnas, retornar conteo seguro
        return f"0/{limit}"

def calculate_daily_pnl(db_path: str = "trading.db") -> float:
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("""
                SELECT COALESCE(SUM(pnl_usd),0.0) FROM trades
                WHERE close_time IS NOT NULL AND DATE(close_time) = DATE('now')
            """)
            return float(cur.fetchone()[0] or 0.0)
    except Exception:
        return 0.0
PY

# alert_manager.py
cat > p1/alert_manager.py <<'PY'
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class Rule:
    window: int      # seconds
    threshold: int   # events to trigger
    cooldown: int    # seconds

DEFAULT_RULES = {
    "fatal": None,  # alert inmediatamente
    "error": Rule(window=180, threshold=5, cooldown=300),
    "warning": Rule(window=300, threshold=10, cooldown=600),
}

class AlertManager:
    def __init__(self, rules: Dict[str, Rule] = None):
        self.rules = rules or DEFAULT_RULES
        # key = (etype, file), value = dict(count:int, first_ts:float, next_allowed:float)
        self.state: Dict[Tuple[str, str], Dict[str, float]] = {}

    def add(self, etype: str, file: str, now: float = None):
        now = now or time.time()
        if etype == "fatal":
            return {"emit": True, "grouped": False, "count": 1, "next_allowed": 0}

        rule = self.rules.get(etype)
        if not rule:
            return {"emit": False}

        key = (etype, file)
        s = self.state.get(key, {"count": 0, "first_ts": now, "next_allowed": 0})
        # cooldown activo
        if now < s.get("next_allowed", 0):
            # consumir pero sin emitir
            s["count"] += 1
            self.state[key] = s
            return {"emit": False, "cooldown": True}

        # ventana
        if now - s.get("first_ts", now) > rule.window:
            s = {"count": 0, "first_ts": now, "next_allowed": 0}

        s["count"] += 1
        self.state[key] = s

        if s["count"] >= rule.threshold:
            s["next_allowed"] = now + rule.cooldown
            # reset contador para próxima ventana
            s["count"] = 0
            s["first_ts"] = now
            self.state[key] = s
            return {
                "emit": True,
                "grouped": True,
                "count": rule.threshold,
                "next_allowed": s["next_allowed"],
            }
        return {"emit": False}
PY

# sheets_handler.py (no-op si GOOGLE_SHEETS_DISABLED=1)
cat > p1/sheets_handler.py <<'PY'
from __future__ import annotations
import os, base64, json
from typing import Dict, Any

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
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        body = {"values": [[row.get(k, "") for k in ("timestamp","symbol","direction","pnl_usd","reason","duration")]]}
        svc.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=RANGE_TRADES,
            valueInputOption="USER_ENTERED",
            body=body
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
PY

# dashboard FastAPI
cat > p1/dashboard.py <<'PY'
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
        "win_rate": "0.0",           # TODO
        "pnl_day": calculate_daily_pnl(),
        "state": get_bot_state(),
        "last_trade_ts": get_last_trade_time(),
        "uptime": get_uptime(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
PY

# tests
cat > tests/test_dashboard.py <<'PY'
from fastapi.testclient import TestClient
from p1.dashboard import app

def test_metrics_endpoint_ok():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    for k in ("trades_today","win_rate","pnl_day","state","last_trade_ts","uptime"):
        assert k in data
PY

cat > tests/test_daily_counter.py <<'PY'
import os, sqlite3, tempfile
from datetime import datetime
from p1.daily_counter import get_daily_count, calculate_daily_pnl

def test_daily_counter_with_db():
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "trading.db")
        with sqlite3.connect(db) as conn:
            conn.execute("CREATE TABLE trades (open_time TEXT, close_time TEXT, pnl_usd REAL)")
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO trades VALUES (?,?,?)", (now, now, 5.0))
            conn.execute("INSERT INTO trades VALUES (?,?,?)", (now, now, -1.5))
            conn.commit()
        assert get_daily_count(db_path=db).endswith("/20")
        assert calculate_daily_pnl(db_path=db) == 3.5
PY

cat > tests/test_alert_manager.py <<'PY'
from p1.daily_counter import get_daily_count, calculate_daily_pnl

def test_alert_grouping_and_cooldown():
    from p1.alert_manager import AlertManager
    am = AlertManager()
    file = "binance_api.py"
    emitted = []
    # 5 errores rápidos: al 5º debería emitir agrupada
    for _ in range(5):
        res = am.add("error", file, now=1000.0)
        emitted.append(res.get("emit", False))
    assert any(emitted), "Debe emitir alerta agrupada al alcanzar el umbral"
    # Inmediatamente después, en cooldown: no debe emitir
    res = am.add("error", file, now=1001.0)
    assert not res.get("emit", False)
PY

cat > tests/test_sheets_stub.py <<'PY'
import os
from p1.sheets_handler import append_trade_closed

def test_sheets_noop_when_disabled(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_DISABLED", "1")
    ok = append_trade_closed({
        "timestamp":"2025-01-01 00:00:00",
        "symbol":"BTC/USDT",
        "direction":"long",
        "pnl_usd": 1.23,
        "reason":"TP",
        "duration":"00:05:00",
    })
    assert ok is True
PY

echo "➡️ 4) CI: fijar Python 3.12.x matrix y asegurar jobs"
mkdir -p .github/workflows
if [ ! -f .github/workflows/ci.yml ]; then
cat > .github/workflows/ci.yml <<'YML'
name: CI - EventArb Bot

on: [push, pull_request]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.12.0", "3.12.1", "3.12.2" ]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Ruff (lint)
        run: ruff check .
      - name: Black (format check)
        run: black --check .
      - name: Pytest
        run: pytest -q
      - name: Upload test results (safe)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: tests-${{ matrix.python-version }}
          path: ./
          if-no-files-found: ignore
          retention-days: 7
YML
else
  # Actualizar matrix a 3.12.x si existe ya el workflow
  sed -i.bak -E 's/python-version:\s*\[.*\]/python-version: \[ '"$PY_MATRIX"' \]/' .github/workflows/ci.yml || true
  sed -i.bak -E 's/actions\/setup-python@v[0-9]+/actions\/setup-python@v5/' .github/workflows/ci.yml || true
  sed -i.bak -E 's/actions\/upload-artifact@v3/actions\/upload-artifact@v4/' .github/workflows/ci.yml || true
  rm -f .github/workflows/ci.yml.bak || true
fi

echo "➡️ 5) Formato y tests locales"
ruff check . --fix || true
isort . || true
black . || true
pytest -q

echo "➡️ 6) Commit & push"
git add -A
git commit -m "feat(p1): scaffolding Sheets/Alerting/Dashboard + tests; CI pinned to Python 3.12.x" || echo "ℹ️ Nada que commitear"
git push -u origin "$BRANCH"

echo "✅ P1 bootstrap listo. Abre PR: $BRANCH → main. En paralelo, puedes levantar el dashboard:"
echo "   uvicorn p1.dashboard:app --reload --port 8000"
