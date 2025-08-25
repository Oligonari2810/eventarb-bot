# 🚀 CHECKLIST DE DESPLIEGUE EN MAINNET

## **🔒 PASO 1: ROTAR SECRETS (CRÍTICO)**

### **Binance API Keys:**
- [ ] Ir a [Binance API Management](https://www.binance.com/en/my/settings/api-management)
- [ ] **REVOCAR** las API keys actuales (ya expuestas en chat)
- [ ] Crear **NUEVAS** API keys con:
  - [ ] Trading habilitado ✅
  - [ ] Withdrawals **DESHABILITADO** ❌
  - [ ] IP whitelist (si es posible) 🔒
- [ ] Copiar nuevas `BINANCE_API_KEY` y `BINANCE_API_SECRET`

### **Telegram Bot Token:**
- [ ] Ir a [@BotFather](https://t.me/botfather) en Telegram
- [ ] `/revoke` el bot token actual
- [ ] Crear **NUEVO** bot con `/newbot`
- [ ] Copiar nuevo `TELEGRAM_BOT_TOKEN`

### **Google Sheets:**
- [ ] Mantener `GOOGLE_SHEETS_CREDENTIALS_B64` actual
- [ ] **NO VOLVER A PUBLICAR** en chats

---

## **⚙️ PASO 2: CONFIGURACIÓN DE PRODUCCIÓN**

### **Crear .env.production:**
```bash
# Copiar .env actual y modificar:
cp .env .env.production

# Cambiar estas variables:
BINANCE_TESTNET=false
SEND_TELEGRAM_ON_PLAN=1
SEND_TELEGRAM_ON_FILL=1
KILL_SWITCH=0
```

### **Verificar .gitignore:**
- [ ] `.env*` incluido ✅
- [ ] `trades.db` incluido ✅
- [ ] `.venv/` incluido ✅

---

## **🧪 PASO 3: TEST DE HUMO**

### **Instalar dependencias:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### **Ejecutar verificación:**
```bash
export $(grep -v '^#' .env.production | xargs)
python check_live_readiness.py
```

### **Resultado esperado:**
```
✅ Sheets OK: X filas leídas
✅ Binance OK: ping {}, X activos con balance
✅ Telegram OK (mensaje enviado)
🎉 ¡TODO LISTO PARA LANZAR EN MAINNET!
```

---

## **🚀 PASO 4: DESPLIEGUE CONTROLADO**

### **Configuración inicial:**
- [ ] `BINANCE_TESTNET=false`
- [ ] `SEND_TELEGRAM_ON_PLAN=1`
- [ ] `SEND_TELEGRAM_ON_FILL=1`
- [ ] `KILL_SWITCH=0`

### **Depósito inicial:**
- [ ] **$500-$1,000 USDT** en Binance
- [ ] Verificar balance disponible
- [ ] Confirmar que no hay restricciones

### **Ejecutar en background:**
```bash
chmod +x run_forever.sh
nohup ./run_forever.sh >> logs/runner.log 2>&1 &
```

### **Monitorear logs:**
```bash
tail -f logs/app.log
```

---

## **📊 PASO 5: VERIFICACIÓN DEL PRIMER TRADE**

### **En Binance:**
- [ ] Orden visible en "Open Orders"
- [ ] Posición visible en "Positions"
- [ ] Stop-loss y take-profit configurados

### **En Base de Datos:**
```bash
sqlite3 trades.db "SELECT * FROM trades ORDER BY created_at DESC LIMIT 1;"
```

### **En Telegram:**
- [ ] Notificación de señal generada
- [ ] Confirmación de trade ejecutado
- [ ] Detalles de entrada, SL, TP

---

## **🔍 PASO 6: MONITOREO CONTINUO**

### **Scripts de monitoreo:**
```bash
# Métricas en tiempo real
python monitor_trades.py

# Backup automático (configurar cron)
./backup_db.sh

# Verificar logs
tail -f logs/app.log
```

### **Cron jobs recomendados:**
```bash
# Backup horario
0 * * * * /ruta/completa/eventarb-bot/backup_db.sh

# Logs diarios
0 0 * * * mv logs/app.log logs/app-$(date +%F).log
```

---

## **🎯 CRITERIOS DE ÉXITO (Primeras 72h)**

### **Operacional:**
- [ ] ≥ 10-20 operaciones ejecutadas sin errores de API
- [ ] Slippage controlado (no rebasar `MAX_SPREAD_BPS`)
- [ ] Telegram y Sheets reportando OK
- [ ] Logs sin errores críticos

### **Financiero:**
- [ ] PnL ligeramente positivo o
- [ ] Drawdown < `DAILY_MAX_LOSS_PCT` (5%)
- [ ] Win rate > 50%

---

## **🚨 PROCEDIMIENTOS DE EMERGENCIA**

### **Parar bot inmediatamente:**
```bash
# Opción 1: Kill switch
echo "KILL_SWITCH=1" >> .env.production
# Reiniciar bot

# Opción 2: Proceso directo
ps aux | grep "app.py"
kill -9 <PID>
```

### **Verificar posiciones:**
```bash
# En Binance: revisar posiciones abiertas
# En DB: verificar estado de trades
python monitor_trades.py
```

---

## **📈 PRÓXIMAS MEJORAS (Después de estabilización)**

- [ ] **Resumen diario automático** a Sheets + Telegram
- [ ] **Canal de señales privado** (monetización)
- [ ] **Docker** para despliegue limpio
- [ ] **Dashboard web** de monitoreo
- [ ] **Alertas de riesgo** avanzadas

---

## **✅ ESTADO FINAL**

**¡EventArb Bot operando en MAINNET con:**
- [ ] Todas las integraciones funcionando
- [ ] Sistema de riesgo implementado
- [ ] Monitoreo y backup automático
- [ ] Kill switch operativo
- [ ] Logs y métricas visibles

**🎉 ¡LISTO PARA PRODUCCIÓN! 🎉**
