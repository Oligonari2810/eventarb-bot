# EventArb Bot - Arbitraje de Eventos Programados

Sistema automatizado de trading para eventos económicos y noticias programadas.

## 🚀 Quickstart

### 1. Instalación
```bash
git clone https://github.com/Oligonari2810/eventarb-bot.git
cd eventarb-bot
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configuración
Editar `.env` con tus credenciales:
```env
GOOGLE_SHEETS_CREDENTIALS_B64=tu_credencial_base64
EVENT_SHEET_ID=tu_sheet_id
BINANCE_API_KEY=tu_api_key
BINANCE_API_SECRET=tu_api_secret
```

### 3. Ejecución
```bash
# Modo normal
python app.py

# Modo continuo
chmod +x run_forever.sh
./run_forever.sh

# Backtesting
python scripts/backtest_demo.py

# Health Check
python scripts/healthcheck.py
```

## 🐳 Docker Deployment
```bash
docker-compose up -d
```

## 📋 Changelog

### v0.6.0 - Semana 6
- Dockerización completa
- Systemd service unit
- Health checks integrados

### v0.5.0 - Semana 5  
- Google Sheets logging
- Límites diarios automáticos
- Health check service

### v0.4.0 - Semana 4
- SL/TP Manager con OCO emulado
- Sistema de métricas y reintentos
- Nudge automático de precios

### v0.3.0 - Semana 3
- Motor de backtesting
- Métricas de performance
- Datos sample incluidos

### v0.2.0 - Semana 2
- Risk Manager con sizing automático
- Paper trading en Testnet
- SQLite database con WAL

### v0.1.0 - Semana 1
- MVP inicial con Google Sheets
- Planner de eventos básico
- Sistema de logging unificado

## 📊 Estructura
```
eventarb-bot/
├── app.py                 # Entry point principal
├── config/               # Configuración YAML
├── eventarb/             # Módulos principales
├── scripts/              # Scripts utilitarios
├── logs/                 # Logs de aplicación
└── ops/                  # Configuración de despliegue
```

## ⚠️ Notas
- Modo simulación por defecto
- Requiere Python 3.11+
- Todas las credenciales via environment variables
