#!/bin/bash
# === RUNNER CON ENTORNO VIRTUAL ===

echo "🚀 Iniciando EventArb Bot Runner con entorno virtual..."

# Activar entorno virtual
source venv/bin/activate

# Configurar modo testnet
export BOT_MODE=testnet

# Limpiar logs
mkdir -p logs
: > logs/app.log
: > logs/runner.log

echo "✅ Entorno virtual activado: $(which python)"
echo "✅ BOT_MODE: $BOT_MODE"
echo "✅ Logs limpiados"

# Ejecutar runner en background
echo "🔄 Iniciando runner.py..."
nohup python -u runner.py >> logs/runner.log 2>&1 &

# Obtener PID del runner
RUNNER_PID=$!
echo "✅ Runner iniciado con PID: $RUNNER_PID"

# Esperar un momento y verificar estado
sleep 3
echo "📊 Estado del sistema:"
ps aux | grep "python.*runner.py" | grep -v grep || echo "❌ Runner no encontrado"

echo ""
echo "🔍 Para monitorear:"
echo "   # Logs del runner:"
echo "   tail -f logs/runner.log"
echo ""
echo "   # Logs de la app:"
echo "   tail -f logs/app.log"
echo ""
echo "   # Estado del sistema:"
echo "   ps aux | grep python | grep -v grep"
