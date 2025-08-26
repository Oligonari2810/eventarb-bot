#!/bin/bash
# === MONITOREO COMPLETO DEL SISTEMA EVENTARB ===

echo "🚀 Abriendo terminales de monitoreo..."

# Terminal 1 - Logs generales (sin filtrar)
echo "📊 Terminal 1: Logs generales (app.log)"
osascript -e 'tell application "Terminal" to do script "cd /Users/anamarperezmarrero/eventarb-bot/eventarb-bot && echo \"=== MONITOREO GENERAL ===\" && tail -f logs_cursor/app.log"'

# Terminal 2 - Solo errores y warnings
echo "⚠️  Terminal 2: Solo errores y warnings"
osascript -e 'tell application "Terminal" to do script "cd /Users/anamarperezmarrero/eventarb-bot/eventarb-bot && echo \"=== SOLO ERRORES Y WARNINGS ===\" && tail -f logs_cursor/app.log | grep -E \"ERROR|WARNING\""'

# Terminal 3 - Monitor del runner
echo "🔄 Terminal 3: Monitor del runner"
osascript -e 'tell application "Terminal" to do script "cd /Users/anamarperezmarrero/eventarb-bot/eventarb-bot && echo \"=== MONITOR DEL RUNNER ===\" && tail -f logs_cursor/runner.log"'

# Terminal 4 - Estado del sistema (procesos, logs en tiempo real)
echo "📈 Terminal 4: Estado del sistema"
osascript -e 'tell application "Terminal" to do script "cd /Users/anamarperezmarrero/eventarb-bot/eventarb-bot && echo \"=== ESTADO DEL SISTEMA ===\" && watch -n 5 \"ps aux | grep python | grep -v grep; echo; echo \"=== LOGS ACTUALES ===\"; tail -n 5 logs_cursor/app.log; echo; tail -n 5 logs_cursor/runner.log\""'

echo "✅ Terminales de monitoreo abiertas:"
echo "   📊 Terminal 1: Logs generales"
echo "   ⚠️  Terminal 2: Solo errores/warnings"
echo "   🔄 Terminal 3: Monitor del runner"
echo "   📈 Terminal 4: Estado del sistema"

echo ""
echo "🔍 Para monitoreo manual en esta terminal:"
echo "   # Logs generales:"
echo "   tail -f logs_cursor/app.log"
echo ""
echo "   # Solo errores:"
echo "   tail -f logs_cursor/app.log | grep -E \"ERROR|WARNING\""
echo ""
echo "   # Runner:"
echo "   tail -f logs_cursor/runner.log"
echo ""
echo "   # Estado del sistema:"
echo "   ps aux | grep python | grep -v grep"
