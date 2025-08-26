#!/usr/bin/env bash

# Activar entorno virtual
source .venv/bin/activate

# Crear directorio de logs
mkdir -p logs

echo "EventArBOT iniciado en $(date)"

# Bucle principal
while true; do
    TS=$(date '+%Y-%m-%d_%H-%M-%S')
    LOG_FILE="logs/app_${TS}.log"
    
    echo "[$TS] Iniciando ciclo de trading..." > "$LOG_FILE"
    
    # Ejecutar app.py
    python app.py >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
    
    echo "[$(date '+%F %T')] app.py terminó con código: $EXIT_CODE" >> "$LOG_FILE"
    
    # Pausa antes del siguiente ciclo
    sleep 5
done

