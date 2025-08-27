#!/usr/bin/env python3
"""Script para poblar la tabla events con eventos de prueba"""

import sqlite3
import os
from datetime import datetime, timedelta

def seed_events(db_path: str = "events.db"):
    """Pobla la tabla events con eventos de prueba"""
    
    # Crear eventos de prueba que coincidan con el schema real
    test_events = [
        {
            "id": "test_daily_alert",
            "t0_iso": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "symbol": "BTCUSDT",
            "type": "TEST_ALERT",
            "consensus": '{"action": "alert", "message": "Alerta diaria de prueba"}',
            "enabled": 1
        },
        {
            "id": "test_hourly_check",
            "t0_iso": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "symbol": "ETHUSDT", 
            "type": "TEST_CHECK",
            "consensus": '{"action": "check", "message": "Verificación horaria de prueba"}',
            "enabled": 1
        },
        {
            "id": "test_weekly_report",
            "t0_iso": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "symbol": "ADAUSDT",
            "type": "TEST_REPORT",
            "consensus": '{"action": "report", "message": "Reporte semanal de prueba"}',
            "enabled": 1
        }
    ]
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Insertar eventos
            for event in test_events:
                conn.execute("""
                    INSERT OR REPLACE INTO events 
                    (id, t0_iso, symbol, type, consensus, enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event["id"],
                    event["t0_iso"],
                    event["symbol"], 
                    event["type"],
                    event["consensus"],
                    event["enabled"]
                ))
            
            conn.commit()
            print(f"✅ {len(test_events)} eventos de prueba insertados")
            
            # Verificar inserción
            cur = conn.execute("SELECT COUNT(*) FROM events")
            count = cur.fetchone()[0]
            print(f"📊 Total de eventos en BD: {count}")
            
    except Exception as e:
        print(f"❌ Error sembrando eventos: {e}")

if __name__ == "__main__":
    seed_events()
