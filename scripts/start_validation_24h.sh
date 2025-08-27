#!/bin/bash
# Script de inicio para validación de 24h

set -e

echo "🎯 EVENTARB BOT - VALIDACIÓN DE 24H"
echo "====================================="
echo "⏰ Duración: 24 horas completas"
echo "🔍 Objetivos:"
echo "  - Ver 1 ciclo completo de ejecuciones"
echo "  - Validar idempotencia"
echo "  - Verificar sin errores de DB"
echo "  - Confirmar alertas a tiempo"
echo "  - Verificar heartbeats continuos"
echo ""

# Verificar virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment no encontrado. Creando..."
    python3 -m venv .venv
fi

# Activar virtual environment
echo "🔧 Activando virtual environment..."
source .venv/bin/activate

# Verificar dependencias
echo "📦 Verificando dependencias..."
pip install -r requirements.txt

# Verificar base de datos
if [ ! -f "events.db" ]; then
    echo "🗄️ Inicializando base de datos..."
    sqlite3 events.db < eventarb/storage/schema.sql
fi

# Verificar eventos de prueba
echo "🌱 Verificando eventos de prueba..."
python scripts/seed_events.py

# Crear directorio de logs
mkdir -p logs

# Configurar variables de entorno para validación
export EMERGENCY_STOP=0
export DRY_RUN=1  # Testing mode
export BOT_MODE=testnet
export DB_PATH=events.db
export PYTHONPATH=$(pwd)

echo "🔧 Variables de entorno configuradas:"
echo "  - EMERGENCY_STOP: $EMERGENCY_STOP"
echo "  - DRY_RUN: $DRY_RUN (Testing mode)"
echo "  - BOT_MODE: $BOT_MODE"
echo "  - DB_PATH: $DB_PATH"

echo ""
echo "🚀 INICIANDO VALIDACIÓN DE 24H..."
echo "📝 Logs disponibles en:"
echo "  - Console: Tiempo real"
echo "  - Archivo: logs/validation_24h.log"
echo ""
echo "🔧 Para detener: Ctrl+C"
echo "⏰ La validación continuará hasta completar 24h o ser interrumpida"
echo ""

# Iniciar validación
python scripts/validation_24h.py
