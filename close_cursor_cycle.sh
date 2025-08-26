#!/bin/bash
# === CIERRA EL CICLO DESDE CURSOR: MERGE + TAG + SOAK TEST + ISSUES P1 ===
set -euo pipefail

REPO_URL="https://github.com/Oligonari2810/eventarb-bot.git"
FEATURE_BRANCH="feat/cursor-evidence"
TAG="v0.1.0"

echo "➡️ 1) Preparar repo local"
git remote -v || git remote add origin "$REPO_URL"
git fetch origin

echo "➡️ 1a) MERGE de ${FEATURE_BRANCH} → main (sin pasar por la web)"
git checkout main
git pull --ff-only origin main || true
# Trae la rama remota y haz merge sin fast-forward para dejar commit de merge claro:
git fetch origin "${FEATURE_BRANCH}:${FEATURE_BRANCH}" || true
git merge --no-ff "${FEATURE_BRANCH}" -m "Merge ${FEATURE_BRANCH} (logging/streams hardened + paridad Cursor)"
git push origin main

echo "➡️ 1b) Crear tag de release ${TAG}"
git tag -a "${TAG}" -m "Release ${TAG}: Logging/streams hardening + paridad Cursor"
git push origin "${TAG}"

echo "✅ Merge y tag listos."

echo "➡️ 2) Soak test en testnet (runner en background, logs limpios)"
export BOT_MODE=testnet
mkdir -p logs
: > logs/app.log
: > logs/runner.log
# Lanza runner en segundo plano
nohup python -u runner.py >> logs/runner.log 2>&1 &
sleep 3
echo "Procesos Python:"
ps aux | grep "python" | grep -v grep || true

echo "➡️ 3) Validación de negocio rápida"
echo "— TRADE_OPENED/CLOSED (últimas 30 líneas):"
tail -n 300 logs/app.log | grep -E "TRADE_(OPENED|CLOSED)" | tail -n 30 || echo "Aún sin TRADE_*; deja correr el bot."
echo "— Límite diario / reinicio:"
grep -Eh "DAILY_LIMIT_REACHED|DAILY_RESTART" logs/* || echo "Aún no alcanzado el límite diario."
echo "— Alertas agrupadas:"
grep -Eh "ALERT_GROUPED" logs/runner.log || echo "Sin alertas agrupadas (OK si no hubo fallos)."
echo "— Streams errors:"
grep -r "Bad file descriptor\|OSError.*9\|init_sys_streams" logs/ || echo "✅ Sin errores de streams"

echo "➡️ 4) Crear issues P1 (si tienes GitHub CLI 'gh' autenticado)"
if command -v gh >/dev/null 2>&1; then
  gh issue create -t "P1: Daily PnL Summary & Evidence (Sheets)" -b $'# Objetivo\nResumen diario automático: date, trades_closed, pnl_usd_sum, pnl_usd_mean, win_rate, max_dd_intraday, fees_usd, notes.\nAppend de cada TRADE_CLOSED a pestaña TradesClosed. Guardar evidence_YYYY-MM-DD.log con todas las líneas TRADE_CLOSED.\n\n# DoD\n- Fila diaria en DailySummary\n- Fila por cierre en <5s\n- evidence_YYYY-MM-DD.log completo\n- Reintento/backoff si falla Sheets\n'
  gh issue create -t "P1: Alerting agrupado + cooldown" -b $'# Objetivo\nEvitar spam: agrupar por {tipo_error, archivo}. Ventana 3 min, umbral ≥5, cooldown 5 min. FATAL inmediato.\n\n# DoD\n- 8 errores en 3 min => 1 alerta ALERT_GROUPED con count y next_allowed_at\n- FATAL alerta inmediata\n'
  gh issue create -t "P1: Heartbeat/Runner health" -b $'# Objetivo\nhealth.json cada 30s con ts, runner_pid, app_pid, last_trade_ts, trades_today, state(OK|PAUSED|RESTARTING). Relanzar app salvo PAUSED por límite diario.\n\n# DoD\n- health.json actualizado\n- Al matar app, runner relanza y state pasa RESTARTING→OK\n- En DAILY_LIMIT_REACHED, state=PAUSED sin relanzar hasta reinicio programado\n'
  echo "✅ Issues P1 creados."
else
  echo "ℹ️ No se encontró 'gh'. Puedes crear los issues P1 desde la web copiando los textos anteriores."
fi

echo "➡️ 5) (Opcional) Gate a real - variables de seguridad sugeridas"
cat <<'ENV'
# .env ejemplo para producción segura (ilustrativo)
KILL_SWITCH=0
DAILY_TRADE_LIMIT=20
MAX_OPEN_TRADES=3
MAX_NOTIONAL_USD=50
MAX_LOSS_DAY_USD=20
COOLDOWN_AFTER_LOSS_MIN=15
ENV

echo "➡️ 6) Chuleta de operación diaria"
echo "— Estado rápido: ps / tail logs"
echo "— Pausa runner con gracia: pkill -SIGTERM -f 'python.*runner.py'"
echo "— Rotación manual segura: : > logs/app.log && : > logs/runner.log"

echo "🎉 Todo listo. Deja al bot corriendo para capturar TRADE_CLOSED y validar PnL."
