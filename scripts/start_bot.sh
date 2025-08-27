#!/bin/bash
# Script de inicio manual para EventArb Bot

set -e

echo "🎯 EVENTARB BOT - INICIO MANUAL"
echo "================================="

# Verificar virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment no encontrado. Creando..."
    python3 -m venv .venv
fi

# Activar virtual environment
echo "🔧 Activando virtual environment..."
source .venv/bin/activate

# Instalar dependencias si es necesario
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

# Configurar variables de entorno
export EMERGENCY_STOP=0
export DRY_RUN=0  # Cambiar a 1 para testing
export BOT_MODE=testnet  # Cambiar a mainnet para producción
export DB_PATH=events.db
export PYTHONPATH=$(pwd)

echo "🔧 Variables de entorno configuradas:"
echo "  - EMERGENCY_STOP: $EMERGENCY_STOP"
echo "  - DRY_RUN: $DRY_RUN"
echo "  - BOT_MODE: $BOT_MODE"
echo "  - DB_PATH: $DB_PATH"

# Iniciar automatización
echo "🚀 Iniciando automatización completa..."
echo "📝 Logs disponibles en logs/app.log"
echo "🔧 Para detener: Ctrl+C"
echo ""

python scripts/start_automation.py
