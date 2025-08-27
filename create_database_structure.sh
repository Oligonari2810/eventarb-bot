#!/bin/bash

echo "🔄 Creando estructura de base de datos completa para trading..."
echo "📁 Creando directorios de datos históricos..."

# Crear estructura de directorios
mkdir -p historical_data/{macro,token_events,market,onchain}
mkdir -p database/backups
mkdir -p logs/validation

echo "🗄️ Inicializando base de datos SQLite con estructura completa..."

# Inicializar SQLite con todas las tablas necesarias
python3 -c "
import sqlite3
import os
from datetime import datetime, timedelta

print('🔧 Creando base de datos trading_data.db...')

# Crear conexión
conn = sqlite3.connect('trading_data.db')
cursor = conn.cursor()

# Tabla principal de eventos con todas las columnas necesarias
cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    family TEXT NOT NULL,
    event_date TEXT NOT NULL,
    t0_iso TEXT NOT NULL,
    symbol TEXT DEFAULT 'BTCUSDT',
    consensus REAL,
    actual REAL,
    deviation REAL,
    impact TEXT,
    executed INTEGER DEFAULT 0,
    outcome TEXT,
    pnl REAL,
    execution_time_ms INTEGER,
    spread_bps REAL,
    slippage_bps REAL,
    book_depth_usd REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabla de eventos macroeconómicos específicos
cursor.execute('''
CREATE TABLE IF NOT EXISTS macro_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    family TEXT DEFAULT 'macro_US',
    event_date TEXT NOT NULL,
    consensus REAL,
    actual REAL,
    deviation REAL,
    surprise_bps INTEGER,
    impact TEXT,
    market_reaction REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabla de token events (unlocks, listings, etc.)
cursor.execute('''
CREATE TABLE IF NOT EXISTS token_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    family TEXT DEFAULT 'crypto_events',
    token_symbol TEXT NOT NULL,
    event_date TEXT NOT NULL,
    description TEXT,
    impact_score REAL,
    supply_affected REAL,
    market_cap_usd REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabla de market data para análisis
cursor.execute('''
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    spread_bps REAL,
    book_depth_usd REAL,
    volatility REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabla de trades ejecutados
cursor.execute('''
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price REAL,
    exit_price REAL,
    size REAL,
    pnl REAL,
    entry_time TEXT,
    exit_time TEXT,
    execution_time_ms INTEGER,
    spread_bps REAL,
    slippage_bps REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events (id)
)
''')

# Tabla de calibraciones del sistema
cursor.execute('''
CREATE TABLE IF NOT EXISTS calibrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family TEXT NOT NULL,
    calibration_date TEXT NOT NULL,
    parameters_before TEXT,
    parameters_after TEXT,
    metrics_before TEXT,
    metrics_after TEXT,
    improvement REAL,
    approver TEXT,
    approved_at TEXT,
    data_hash TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

# Tabla de snapshots para rollback
cursor.execute('''
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calibration_id INTEGER,
    snapshot_date TEXT NOT NULL,
    parameters TEXT,
    metrics TEXT,
    data_hash TEXT,
    rollback_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (calibration_id) REFERENCES calibrations (id)
)
''')

# Crear índices para performance
cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_family ON events (family)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_executed ON events (executed)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_date ON events (event_date)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_time ON trades (entry_time)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_calibrations_family ON calibrations (family)')

# Insertar datos de ejemplo para testing
print('📊 Insertando datos de ejemplo para validación...')

# Eventos macro de ejemplo (últimos 12 meses)
macro_examples = [
    ('CPI', 'macro_US', '2024-01-15', 3.2, 3.5, 0.3, 30, 'HIGH', 0.025),
    ('CPI', 'macro_US', '2024-02-15', 3.1, 3.3, 0.2, 20, 'HIGH', 0.018),
    ('CPI', 'macro_US', '2024-03-15', 3.0, 2.8, -0.2, -20, 'MEDIUM', -0.015),
    ('FOMC', 'macro_US', '2024-01-31', 5.25, 5.25, 0.0, 0, 'LOW', 0.005),
    ('FOMC', 'macro_US', '2024-03-20', 5.25, 5.25, 0.0, 0, 'LOW', 0.003),
    ('GDP', 'macro_US', '2024-01-25', 2.1, 1.8, -0.3, -30, 'HIGH', -0.022),
    ('GDP', 'macro_US', '2024-04-25', 2.0, 2.2, 0.2, 20, 'MEDIUM', 0.018),
    ('UNEMPLOYMENT', 'macro_US', '2024-02-02', 3.7, 3.8, 0.1, 10, 'MEDIUM', 0.012),
    ('UNEMPLOYMENT', 'macro_US', '2024-03-01', 3.8, 3.9, 0.1, 10, 'MEDIUM', 0.008),
    ('UNEMPLOYMENT', 'macro_US', '2024-04-05', 3.9, 3.8, -0.1, -10, 'MEDIUM', -0.015),
    ('ECB_RATE', 'macro_EU', '2024-01-25', 4.5, 4.5, 0.0, 0, 'LOW', 0.002),
    ('ECB_RATE', 'macro_EU', '2024-03-07', 4.5, 4.5, 0.0, 0, 'LOW', 0.001),
    ('ECB_RATE', 'macro_EU', '2024-04-11', 4.5, 4.5, 0.0, 0, 'LOW', 0.003)
]

for event in macro_examples:
    cursor.execute('''
        INSERT INTO macro_events (event_type, family, event_date, consensus, actual, deviation, surprise_bps, impact, market_reaction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', event)

# Token events de ejemplo (últimos 6 meses)
token_examples = [
    ('UNLOCK', 'crypto_unlocks', 'BTC', '2024-01-15', 'Monthly BTC unlock', 0.7, 0.001, 850000000000),
    ('UNLOCK', 'crypto_unlocks', 'BTC', '2024-02-15', 'Monthly BTC unlock', 0.7, 0.001, 820000000000),
    ('UNLOCK', 'crypto_unlocks', 'BTC', '2024-03-15', 'Monthly BTC unlock', 0.7, 0.001, 780000000000),
    ('UNLOCK', 'crypto_unlocks', 'ETH', '2024-01-15', 'Monthly ETH unlock', 0.6, 0.002, 320000000000),
    ('UNLOCK', 'crypto_unlocks', 'ETH', '2024-02-15', 'Monthly ETH unlock', 0.6, 0.002, 310000000000),
    ('UNLOCK', 'crypto_unlocks', 'ETH', '2024-03-15', 'Monthly ETH unlock', 0.6, 0.002, 300000000000),
    ('LISTING', 'listings', 'NEW_TOKEN', '2024-01-10', 'Binance listing', 0.8, 0.0, 50000000),
    ('LISTING', 'listings', 'ANOTHER_TOKEN', '2024-02-20', 'Coinbase listing', 0.7, 0.0, 30000000),
    ('LISTING', 'listings', 'THIRD_TOKEN', '2024-03-15', 'Kraken listing', 0.6, 0.0, 20000000),
    ('HACK', 'security_incidents', 'EXCHANGE_A', '2024-01-05', 'Major exchange hack', 0.9, 0.0, 0),
    ('HACK', 'security_incidents', 'DEFI_PROTOCOL', '2024-02-10', 'DeFi exploit', 0.8, 0.0, 0)
]

for event in token_examples:
    cursor.execute('''
        INSERT INTO token_events (event_type, family, token_symbol, event_date, description, impact_score, supply_affected, market_cap_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', event)

# Market data de ejemplo (últimos 30 días)
market_examples = []
base_date = datetime.now() - timedelta(days=30)
for i in range(30):
    date = base_date + timedelta(days=i)
    market_examples.append((
        'BTCUSDT', date.strftime('%Y-%m-%d %H:%M:%S'),
        45000 + i*100, 45100 + i*100, 44900 + i*100, 45050 + i*100,
        1000000 + i*10000, 2.5, 5000000, 0.025
    ))

for data in market_examples:
    cursor.execute('''
        INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume, spread_bps, book_depth_usd, volatility)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

# Commit y cerrar
conn.commit()
conn.close()

print('✅ Base de datos inicializada correctamente')
print('📊 Datos de ejemplo insertados:')
print('   - Macro events: 13 eventos (CPI, FOMC, GDP, Unemployment, ECB)')
print('   - Token events: 10 eventos (Unlocks, Listings, Hacks)')
print('   - Market data: 30 días de datos BTC')
print('')
print('🔍 Próximo paso: Ejecutar validate_data_coverage.py')
"
