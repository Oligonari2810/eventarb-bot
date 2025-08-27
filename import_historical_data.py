#!/usr/bin/env python3
"""
Script para importar datos históricos desde múltiples fuentes
Incluye datos macroeconómicos, token events y market data
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json

def import_macro_data():
    """Importar datos macroeconómicos históricos"""
    print("📊 Importando datos macroeconómicos...")
    
    # Datos de ejemplo (luego reemplazar con APIs reales)
    macro_data = [
        {'event_type': 'CPI', 'family': 'macro_US', 'event_date': '2024-01-15', 'consensus': 3.2, 'actual': 3.5, 'deviation': 0.3, 'impact': 'HIGH'},
        {'event_type': 'GDP', 'family': 'macro_US', 'event_date': '2024-01-25', 'consensus': 2.1, 'actual': 1.8, 'deviation': -0.3, 'impact': 'HIGH'},
        {'event_type': 'FOMC', 'family': 'macro_US', 'event_date': '2024-01-31', 'consensus': 5.25, 'actual': 5.25, 'deviation': 0.0, 'impact': 'LOW'},
        {'event_type': 'UNEMPLOYMENT', 'family': 'macro_US', 'event_date': '2024-02-02', 'consensus': 3.7, 'actual': 3.8, 'deviation': 0.1, 'impact': 'MEDIUM'},
        {'event_type': 'ECB_RATE', 'family': 'macro_EU', 'event_date': '2024-01-25', 'consensus': 4.5, 'actual': 4.5, 'deviation': 0.0, 'impact': 'LOW'}
    ]
    
    conn = sqlite3.connect('trading_data.db')
    df = pd.DataFrame(macro_data)
    df.to_sql('macro_events', conn, if_exists='append', index=False)
    conn.close()
    print(f"✅ Importados {len(macro_data)} eventos macro")

def import_token_events():
    """Importar token events históricos"""
    print("🪙 Importando token events...")
    
    token_events = [
        {'event_type': 'UNLOCK', 'family': 'crypto_unlocks', 'token_symbol': 'BTC', 'event_date': '2024-01-15', 'description': 'Monthly unlock', 'impact_score': 0.7},
        {'event_type': 'LISTING', 'family': 'listings', 'token_symbol': 'NEW_TOKEN', 'event_date': '2024-01-10', 'description': 'Binance listing', 'impact_score': 0.8},
        {'event_type': 'HACK', 'family': 'security_incidents', 'token_symbol': 'EXCHANGE_A', 'event_date': '2024-01-05', 'description': 'Major exchange hack', 'impact_score': 0.9}
    ]
    
    conn = sqlite3.connect('trading_data.db')
    df = pd.DataFrame(token_events)
    df.to_sql('token_events', conn, if_exists='append', index=False)
    conn.close()
    print(f"✅ Importados {len(token_events)} token events")

if __name__ == "__main__":
    import_macro_data()
    import_token_events()
    print("🎯 Datos históricos importados correctamente")
