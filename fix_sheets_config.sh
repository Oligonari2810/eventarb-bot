#!/bin/bash

echo "🔧 CORRIGIENDO CONFIGURACIÓN DE SHEETS"
echo "======================================"

# Backup del archivo actual
cp .env.production .env.production.backup.$(date +%Y%m%d_%H%M%S)

echo "✅ Backup creado: .env.production.backup.*"

# Corregir rangos para usar pestañas distintas
sed -i.bak 's/^EVENT_SHEET_RANGE=.*/EVENT_SHEET_RANGE=Events!A2:G200/' .env.production
sed -i.bak 's/^TRADES_SHEET_RANGE=.*/TRADES_SHEET_RANGE=Trades!A2:L2000/' .env.production

echo "✅ EVENT_SHEET_RANGE corregido a: Events!A2:G200"
echo "✅ TRADES_SHEET_RANGE corregido a: Trades!A2:L2000"

echo ""
echo "📋 CONFIGURACIÓN ACTUALIZADA:"
echo "EVENT_SHEET_ID: $(grep EVENT_SHEET_ID .env.production)"
echo "TRADES_SHEET_ID: $(grep TRADES_SHEET_ID .env.production)"
echo "EVENT_SHEET_RANGE: $(grep EVENT_SHEET_RANGE .env.production)"
echo "TRADES_SHEET_RANGE: $(grep TRADES_SHEET_RANGE .env.production)"

echo ""
echo "🔍 VERIFICANDO CONFIGURACIÓN..."
export $(grep -v '^#' .env.production | xargs)
python audit_config.py

echo ""
echo "📝 PRÓXIMOS PASOS:"
echo "1. En Google Sheets, crear pestaña 'Events' con columnas: id|kind|t0_iso|symbols_csv|consensus|note|enabled"
echo "2. Crear pestaña 'Trades' con columnas: id|symbol|side|quantity|entry_price|tp_price|sl_price|risk_pct|enabled|created_at|closed_at|pnl_usd"
echo "3. Mover eventos válidos a pestaña 'Events'"
echo "4. Proteger pestaña 'Events' (solo lectura para el bot)"
echo "5. Ejecutar: python check_live_readiness.py"

