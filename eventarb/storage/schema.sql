-- SQLite schema for EventArb trades
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity_cents INTEGER NOT NULL,  -- Changed from REAL to INTEGER cents
    entry_price_cents INTEGER NOT NULL,  -- Changed from REAL to INTEGER cents
    tp_price_cents INTEGER,  -- Changed from REAL to INTEGER cents
    sl_price_cents INTEGER,  -- Changed from REAL to INTEGER cents
    notional_usd_cents INTEGER NOT NULL,  -- Changed from REAL to INTEGER cents
    simulated BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trades_event ON trades (event_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);
CREATE INDEX IF NOT EXISTS idx_trades_created ON trades (created_at);

-- Event fires table with idempotency fix
CREATE TABLE IF NOT EXISTS event_fires (
    event_id TEXT NOT NULL,
    window_sec INTEGER NOT NULL,  -- Changed from fired_at to window_sec for idempotency
    fired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, window_sec)  -- Changed from (event_id, fired_at)
);

-- Bot state persistence table
CREATE TABLE IF NOT EXISTS bot_state (
    date TEXT PRIMARY KEY,  -- Date in YYYY-MM-DD format
    trades_done INTEGER DEFAULT 0,
    loss_cents INTEGER DEFAULT 0,
    max_trades_per_day INTEGER DEFAULT 20,
    daily_loss_limit_cents INTEGER DEFAULT 10000,  -- $100.00 in cents
    emergency_stop BOOLEAN DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Events table (if not exists)
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    t0_iso TEXT NOT NULL,        -- Timestamp ISO en UTC
    symbol TEXT NOT NULL,         -- Ej: BTCUSDT
    type TEXT NOT NULL,           -- Ej: CPI, FOMC, EARNINGS
    consensus TEXT,               -- JSON opcional
    enabled INTEGER DEFAULT 1     -- 1=activo, 0=inactivo
);

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_event_fires_event ON event_fires (event_id);
CREATE INDEX IF NOT EXISTS idx_event_fires_window ON event_fires (window_sec);
CREATE INDEX IF NOT EXISTS idx_bot_state_date ON bot_state (date);
CREATE INDEX IF NOT EXISTS idx_events_t0 ON events (t0_iso);
CREATE INDEX IF NOT EXISTS idx_events_symbol ON events (symbol);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (type);

