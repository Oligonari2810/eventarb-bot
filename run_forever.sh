#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cargar entorno
set -a
source .env.production
set +a

mkdir -p logs

# Notificar inicio
python3 -c "
import os, datetime
from eventarb.utils.notify import send_telegram
send_telegram('🟢 *EventArb Iniciado*\n' + datetime.datetime.utcnow().isoformat() + ' UTC')
"

while true; do
  TS=$(date '+%Y-%m-%d_%H-%M-%S')
  LOG_FILE="logs/app_${TS}.log"
  
  echo "[$TS] Iniciando app.py..." > "$LOG_FILE"
  
  if [[ "${KILL_SWITCH:-0}" == "1" ]]; then
    echo "KILL_SWITCH=1 → Parada segura" >> "$LOG_FILE"
    python3 -c "from eventarb.utils.notify import send_telegram; send_telegram('⏸️ *EventArb Pausado*\nKill Switch activado')"
    sleep 60
    continue
  fi
  
  # Ejecutar app.py con captura de errores
  python app.py >> "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  
  echo "[$(date '+%F %T')] app.py terminó con código: $EXIT_CODE" >> "$LOG_FILE"
  
  # Notificar si fue por límite diario
  if [ $EXIT_CODE -eq 0 ]; then
    python3 -c "from eventarb.utils.notify import send_telegram; send_telegram('⏹️ *EventArb Reiniciando*\nLímite diario alcanzado')"
  elif [ $EXIT_CODE -ne 0 ]; then
    python3 -c "from eventarb.utils.notify import send_telegram; send_telegram('⚠️ *EventArb Error*\nCódigo de salida: $EXIT_CODE')"
  fi
  
  sleep 5
done

