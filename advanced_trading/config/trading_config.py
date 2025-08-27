"""
Configuración principal del sistema de trading
"""
TRADING_CONFIG = {
    # --- Risk Management ---
    'RISK_PER_TRADE': 0.015,
    'MAX_DAILY_LOSS': 0.05,
    'MAX_DAILY_TRADES': 8,
    'MAX_OPEN_POSITIONS': 3,
    'PER_EVENT_MAX_TRADES': 2,
    'COOLDOWN_SEC': 600,                 # 10 min cooldown tras cerrar trade/evento
    'RESET_TZ': 'America/Chicago',
    'RESET_HOUR_LOCAL': 0,               # reseteo a medianoche local

    # --- Execution / Microestructura ---
    'ATR_TIMEFRAME': '1m',
    'VOLATILITY_LOOKBACK': 20,
    'DEFAULT_SL_MULTIPLIER': 2.0,        # SL = 2 × ATR(1m, 20)
    'DEFAULT_TP_LEVELS': [0.005, 0.01, 0.02],
    'TP_ALLOCATION': [0.4, 0.35, 0.25],  # % de la posición en cada TP
    'MAX_SPREAD_BPS': 3,                 # 3 bps spread máx en el momento de enviar
    'MAX_SLIPPAGE_BPS': 10,              # 10 bps deslizamiento máx tolerado
    'MIN_BOOK_DEPTH_USD': 2_000_000,     # profundidad mínima sumada top levels
    'ORDER_TIMEOUT_SEC': 10,
    'PARTIAL_FILL_POLICY': 'cancel_remaining',  # o 'keep_until_timeout'

    # --- Arbitrage (BTC/ETH) ---
    'CORRELATION_THRESHOLD': 0.8,
    'CORRELATION_LOOKBACK_MIN': 1440,    # 1 día de velas 1m
    'SPREAD_LOOKBACK': 360,              # 6h para zscore
    'ZSCORE_ENTRY': 2.0,
    'ZSCORE_EXIT': 0.5,
    'HEDGE_RATIO': 'rolling_beta',
    'ARBITRAGE_RISK_PCT': 0.01,
    
    # --- Volatility Breakout (OCO bidireccional) ---
    'VOLATILITY_BREAKOUT_ENABLED': True,  # estrategia de breakout bidireccional
    'VOLATILITY_ATR_MULTIPLIER': 2.0,    # multiplicador ATR para niveles OCO
    'VOLATILITY_ENTRY_SIZE': 0.3,        # 30% del tamaño total en breakout
    'VOLATILITY_TP_LEVELS': [0.01, 0.02], # take profit para breakout

    # --- Broker ---
    'BROKER': 'binance',
    'MARKET': 'usdt_perp',
    'ACCOUNT_TYPE': 'futures',
    'MARGIN_MODE': 'isolated',
    'HEDGE_MODE': True,
    'LEVERAGE': 3,

    # --- Monitoring ---
    'HEARTBEAT_INTERVAL': 60,
    'HEALTH_CHECK_INTERVAL': 300,
    'MAX_FEED_LATENCY_MS': 500,          # no operar si el feed viene tarde
    'MAX_FUNDING_BPS': 20,               # evitar entrar si funding > 0.20%/8h
    
    # --- Logging & Auditoría ---
    'LOG_ORDER_BLOCKS': True,            # registrar órdenes bloqueadas por microestructura
    'LOG_MICROSTRUCTURE_VIOLATIONS': True, # registrar violaciones de spread/slippage
    'AUDIT_LOG_RETENTION_DAYS': 30,     # retener logs de auditoría por 30 días
    
    # --- Alertas & Notificaciones ---
    'TELEGRAM_ALERTS_ENABLED': True,     # alertas de Telegram para eventos críticos
    'DASHBOARD_ALERTS_ENABLED': True,    # alertas en dashboard web
    'ALERT_COOLDOWN_ACTIVATED': True,    # alerta cuando se activa cooldown
    'ALERT_DAILY_STOP_REACHED': True,    # alerta cuando se alcanza stop diario
    'ALERT_TRADE_OPEN_CLOSE': True,      # alerta para trades abiertos/cerrados
    
    # --- Filtrado Inteligente & Anti-Ruido ---
    'MAX_EVENTS_PER_HOUR': 10,           # máximo eventos por hora para evitar spam
    'MIN_IMPACT_SCORE': 0.6,             # score mínimo para procesar evento (0.0-1.0)
    'EVENT_DEBOUNCE_SEC': 300,           # 5 min entre eventos similares
    'MAX_SOCIAL_SOURCES': 5,             # máximo fuentes sociales simultáneas
    'NEWS_QUALITY_THRESHOLD': 0.7,      # calidad mínima de noticias (fuentes confiables)
    'DUPLICATE_DETECTION': True,         # detectar eventos duplicados
    
    # --- APIs Consolidadas & Timeouts ---
    'API_TIMEOUT_SEC': 15,               # timeout para todas las APIs externas
    'API_RETRY_ATTEMPTS': 3,             # reintentos en caso de fallo
    'API_RETRY_DELAY_SEC': 5,            # delay entre reintentos
    'PREFERRED_DATA_SOURCES': [          # fuentes de datos preferidas (orden de prioridad)
        'tradingeconomics',              # eventos macro
        'messari',                       # token unlocks
        'thetie',                        # social sentiment
        'coingecko',                     # market data
        'binance'                        # exchange data
    ],
    'FALLBACK_SOURCES': [                # fuentes de respaldo
        'alphavantage',                  # alternativa para macro
        'cryptocompare'                  # alternativa para crypto
    ],
    
    # --- Scoring Inteligente & Reglas Simples ---
    'IMPACT_SCORING_RULES': {
        # Macro Events (reglas simples y claras)
        'CPI': {
            'CRITICAL': 0.2,             # surprise > 0.2% = crítico
            'HIGH': 0.1,                 # surprise > 0.1% = alto
            'MEDIUM': 0.05               # surprise > 0.05% = medio
        },
        'FOMC': {
            'CRITICAL': 0.25,            # rate change > 0.25% = crítico
            'HIGH': 0.125,               # rate change > 0.125% = alto
            'MEDIUM': 0.05               # rate change > 0.05% = medio
        },
        'GDP': {
            'CRITICAL': 0.5,             # surprise > 0.5% = crítico
            'HIGH': 0.25,                # surprise > 0.25% = alto
            'MEDIUM': 0.1                # surprise > 0.1% = medio
        },
        # Crypto Events (reglas simples)
        'TOKEN_UNLOCK': {
            'CRITICAL': 0.10,            # unlock > 10% supply = crítico
            'HIGH': 0.05,                # unlock > 5% supply = alto
            'MEDIUM': 0.02               # unlock > 2% supply = medio
        },
        'LISTING': {
            'CRITICAL': 'major_exchange', # Binance, Coinbase = crítico
            'HIGH': 'tier2_exchange',     # Kraken, KuCoin = alto
            'MEDIUM': 'tier3_exchange'    # otros = medio
        }
    },
    
    'SENTIMENT_WEIGHTS': {               # pesos para scoring de sentimiento
        'SOCIAL_MEDIA': 0.3,             # 30% del score total
        'NEWS_QUALITY': 0.4,             # 40% del score total
        'ON_CHAIN': 0.2,                 # 20% del score total
        'MARKET_DATA': 0.1               # 10% del score total
    },
    
    # --- Auto-Calibración & Ajuste Dinámico ---
    'THRESHOLD_CALIBRATION': {
        'ENABLED': True,                  # habilitar auto-calibración
        'CALIBRATION_PERIOD_DAYS': 14,    # recalibrar cada 2 semanas
        'MIN_DATA_POINTS': 50,            # mínimo datos para recalibrar
        'HISTORICAL_LOOKBACK_DAYS': 90,   # 3 meses de histórico para calibración
        'ADJUSTMENT_FACTOR': 0.1,         # factor de ajuste gradual (10%)
        'MAX_ADJUSTMENT': 0.5             # ajuste máximo permitido (50%)
    },
    'DYNAMIC_THRESHOLDS': {
        'CPI_MOVEMENT_THRESHOLD': 0.02,   # 2% movimiento BTC por CPI surprise
        'FOMC_MOVEMENT_THRESHOLD': 0.03,  # 3% movimiento BTC por FOMC
        'UNLOCK_MOVEMENT_THRESHOLD': 0.05, # 5% movimiento por token unlock
        'VOLATILITY_MOVEMENT_THRESHOLD': 0.04 # 4% movimiento por volatilidad
    },
    
    # --- Calibración por Familias de Evento (Solución a Matices) ---
    'EVENT_FAMILIES': {
        'macro_US': {
            'lookback_days': 365,          # 12 meses para macro US (CPI, FOMC, GDP)
            'min_data_points': 20,         # CPI: ~4 por año, FOMC: ~8 por año
            'calibration_weight': 1.0      # peso completo en calibración
        },
        'macro_EU': {
            'lookback_days': 365,          # 12 meses para macro EU
            'min_data_points': 20,         # ECB, Eurostat
            'calibration_weight': 0.8      # peso reducido (menor impacto en crypto)
        },
        'crypto_unlocks': {
            'lookback_days': 180,          # 6 meses para unlocks
            'min_data_points': 30,         # muchos unlocks por mes
            'calibration_weight': 0.9      # peso alto (impacto directo)
        },
        'listings': {
            'lookback_days': 90,           # 3 meses para listings
            'min_data_points': 25,         # varios listings por mes
            'calibration_weight': 0.7      # peso medio
        },
        'security_incidents': {
            'lookback_days': 180,          # 6 meses para hacks/incidentes
            'min_data_points': 10,         # pocos pero de alto impacto
            'calibration_weight': 0.6      # peso bajo (eventos raros)
        }
    },
    
    'CALIBRATION_GUARDRAILS': {
        'MAX_DELTA_PER_CYCLE': 0.15,      # máximo cambio por ciclo (15%)
        'REQUIRE_MANUAL_APPROVAL': True,   # aprobación manual si > 15%
        'MIN_IMPROVEMENT_THRESHOLD': 0.05, # mejora mínima requerida (5%)
        'ROLLBACK_ON_DEGRADATION': True    # rollback si métricas empeoran
    },
    
    # --- Sistema de Aprobación Manual & Rollback ---
    'MANUAL_APPROVAL': {
        'ENABLED': True,                   # habilitar aprobación manual obligatoria
        'BLOCK_APPLICATION': True,         # BLOQUEAR aplicación si no hay aprobación
        'APPROVAL_TIMEOUT_HOURS': 24,     # timeout de aprobación (24h)
        'REQUIRE_APPROVER_NAME': True,     # requerir nombre del aprobador
        'AUDIT_APPROVAL_LOG': True,        # registrar todas las aprobaciones
        'ESCALATION_LEVELS': [             # niveles de escalación
            'TRADER',                      # trader → supervisor
            'supervisor',                  # supervisor → risk manager
            'RISK_MANAGER'                 # risk manager → CTO
        ]
    },
    
    'SNAPSHOT_ROLLBACK': {
        'ENABLED': True,                   # habilitar sistema de snapshot
        'SAVE_BEFORE_CALIBRATION': True,   # guardar antes de cada calibración
        'PARAMS_FILE': 'params.json',      # archivo de parámetros
        'DATA_HASH_ENABLED': True,         # incluir hash de datos usados
        'ROLLBACK_ENDPOINT': '/api/rollback', # endpoint para rollback inmediato
        'AUTO_ROLLBACK_ON_FAILURE': True,  # rollback automático si falla
        'RETENTION_SNAPSHOTS': 10,         # mantener últimos 10 snapshots
        'SNAPSHOT_METADATA': {             # metadatos del snapshot
            'timestamp': True,             # timestamp de creación
            'calibration_id': True,        # ID de la calibración
            'approver': True,              # quién aprobó
            'metrics_before': True,        # métricas antes del cambio
            'metrics_after': True,         # métricas después del cambio
            'data_hash': True,             # hash de datos usados
            'rollback_reason': True        # razón del rollback (si aplica)
        }
    },
    
    # --- Zonas Horarias (America/Chicago) ---
    'TIMEZONE_CONFIG': {
        'PRIMARY_TIMEZONE': 'America/Chicago', # zona horaria principal
        'INGEST_TIMEZONE': 'America/Chicago',  # ingesta en Chicago
        'SCHEDULER_TIMEZONE': 'America/Chicago', # scheduler en Chicago
        'WALK_FORWARD_TIMEZONE': 'America/Chicago', # walk-forward en Chicago
        'EVENT_WINDOW_TIMEZONE': 'America/Chicago', # ventanas de evento en Chicago
        'BACKUP_TIMEZONE': 'UTC'           # backup en UTC
    },
    
    # --- Feature Flags Recomendados (GO) ---
    'FEATURES': {
        'AUTO_CALIBRATION_ON': True,       # auto-calibración habilitada
        'REQUIRE_MANUAL_APPROVAL': True,   # activa la puerta humana
        'ROLLBACK_ON_DEGRADATION': True,   # rollback automático si empeora
        'HIST_WEIGHTING_ON': True,         # ponderación histórica habilitada
        'BACKTEST_OPT_ON': True,           # optimización por backtest habilitada
        'STOP_RULES_ON': True,             # reglas de parada activas (PF/DD/Sharpe/loss-streak)
        'MICROSTRUCTURE_CHECKS': True,     # verificaciones de microestructura
        'WALK_FORWARD_TESTING': True,      # testing walk-forward habilitado
        'SNAPSHOT_SYSTEM': True,           # sistema de snapshot habilitado
        'REAL_TIME_MONITORING': True       # monitoreo en tiempo real
    },

    'BACKTEST_METRICS': {
        'PRIMARY_METRICS': {
            'PROFIT_FACTOR': 1.1,          # mínimo PF requerido
            'SHARPE_RATIO': 0.5,           # mínimo Sharpe event-window
            'MAX_DRAWDOWN': 0.15,          # máximo drawdown permitido (15%)
            'HIT_RATE_CONDITIONAL': 0.55   # hit-rate solo en ejecuciones (55%)
        },
        'STOP_RULES': {
            'PF_BELOW_THRESHOLD': True,    # parar si PF < 1.1
            'DD_ABOVE_LIMIT': True,        # parar si DD > 15%
            'SHARPE_BELOW_THRESHOLD': True, # parar si Sharpe < 0.5
            'CONSECUTIVE_LOSSES': 5        # parar tras 5 pérdidas consecutivas
        },
        'WALK_FORWARD': {
            'ENABLED': True,                # habilitar walk-forward testing
            'TRAINING_WINDOW_DAYS': 90,    # entrenar con 90 días
            'TESTING_WINDOW_DAYS': 30,     # probar con 30 días
            'STEP_SIZE_DAYS': 30,          # avanzar 30 días por iteración
            'MIN_TRAINING_EVENTS': 20      # mínimo eventos para entrenar
        },
        # --- Fuente de Verdad de Métricas (Solo Trades Ejecutados) ---
        'METRICS_SOURCE': {
            'ONLY_EXECUTED_TRADES': True,   # calcular solo con trades realmente ejecutados
            'EVENT_WINDOW_MINUTES': 15,     # ventana T0 → T0+15m para métricas
            'POST_MICROSTRUCTURE': True,    # métricas después de verificar microestructura
            'EXCLUDE_BLOCKED_ORDERS': True, # excluir órdenes bloqueadas por spread/slippage
            'REAL_FILL_PRICES': True        # usar precios reales de fill, no teóricos
        }
    },
    
    # --- Comprobación de Cobertura Mínima Real ---
    'COVERAGE_VALIDATION': {
        'ENABLED': True,                    # habilitar validación de cobertura
        'CHECK_BEFORE_CALIBRATION': True,   # verificar antes de calibrar
        'SQL_QUERY': """
            SELECT family, COUNT(*) AS n, 
                   SUM(CASE WHEN t0_iso >= datetime('now','-365 days') THEN 1 ELSE 0 END) AS last_365d
            FROM events WHERE executed=1 GROUP BY family
        """,
        'MINIMUM_REQUIREMENTS': {
            'macro_US': {'total': 20, 'last_365d': 15},      # mínimo 20 total, 15 en último año
            'macro_EU': {'total': 15, 'last_365d': 10},      # mínimo 15 total, 10 en último año
            'crypto_unlocks': {'total': 30, 'last_365d': 20}, # mínimo 30 total, 20 en último año
            'listings': {'total': 25, 'last_365d': 15},      # mínimo 25 total, 15 en último año
            'security_incidents': {'total': 10, 'last_365d': 5} # mínimo 10 total, 5 en último año
        },
        'ABORT_ON_INSUFFICIENT_DATA': True, # abortar si no hay suficientes datos
        'LOG_COVERAGE_REPORT': True,        # registrar reporte de cobertura
        'ALERT_INSUFFICIENT_COVERAGE': True # alertar si cobertura insuficiente
    }
}

SYMBOLS_CONFIG = {
    'MAIN': 'BTC/USDT',
    'SECONDARY': 'ETH/USDT',
    'ARBITRAGE_PAIRS': ['BTC/USDT', 'ETH/USDT'],
    'LIQUIDITY_THRESHOLD_USD_PER_MIN': 1_000_000,
}

EVENT_CONFIG = {
    'ENABLED_EVENTS': ['CPI', 'GDP', 'UNEMPLOYMENT', 'INTEREST_RATE', 'RETAIL_SALES'],
    'PRE_EVENT_BUFFER': 600,             # preparar órdenes y freeze si spread > umbral
    'POST_EVENT_WINDOW': 900,            # gestión y cierre en 15 min
    'MIN_SURPRISE_BPS': {'CPI': 10, 'UNEMPLOYMENT': 10, 'GDP': 15},  # gatillos
    'ENTRY_MODE': 'T0And_confirm',      # T0 + confirmación (2 velas) si spread ok
    'CONFIRMATION_BARS': 2,
    'MAX_ENTRY_DELAY_SEC': 120,          # si no confirma en 2min, no se entra
}
