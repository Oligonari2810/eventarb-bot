#!/usr/bin/env python3
"""
Script de monitoreo para EventArb Bot
Verifica el estado de la automatización y eventos
"""

import sqlite3
import os
import time
from datetime import datetime, timedelta

def check_database_status():
    """Verifica el estado de la base de datos"""
    print("🗄️ VERIFICANDO BASE DE DATOS:")
    print("-" * 30)
    
    try:
        with sqlite3.connect("events.db") as conn:
            # Eventos
            events = conn.execute("SELECT COUNT(*) FROM events WHERE enabled = 1").fetchone()[0]
            print(f"📊 Eventos activos: {events}")
            
            # Event fires
            fires = conn.execute("SELECT COUNT(*) FROM event_fires").fetchone()[0]
            print(f"🚀 Eventos disparados: {fires}")
            
            # Bot state
            bot_state = conn.execute("SELECT * FROM bot_state ORDER BY date DESC LIMIT 1").fetchone()
            if bot_state:
                print(f"🤖 Estado del bot: {bot_state}")
            else:
                print("🤖 Estado del bot: No disponible")
                
            # Últimos eventos disparados
            recent_fires = conn.execute("""
                SELECT event_id, window_sec, fired_at 
                FROM event_fires 
                ORDER BY fired_at DESC 
                LIMIT 5
            """).fetchall()
            
            if recent_fires:
                print(f"📅 Últimos eventos disparados: {len(recent_fires)}")
                for fire in recent_fires:
                    print(f"  - {fire[0]} (window: {fire[1]}) at {fire[2]}")
            else:
                print("📅 No hay eventos disparados recientemente")
                
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")

def check_environment():
    """Verifica variables de entorno"""
    print("\n🔧 VERIFICANDO VARIABLES DE ENTORNO:")
    print("-" * 30)
    
    env_vars = [
        "EMERGENCY_STOP",
        "DRY_RUN", 
        "BOT_MODE",
        "DB_PATH",
        "PYTHONPATH"
    ]
    
    for var in env_vars:
        value = os.environ.get(var, "No definida")
        print(f"  {var}: {value}")

def check_upcoming_events():
    """Verifica eventos próximos"""
    print("\n📅 VERIFICANDO EVENTOS PRÓXIMOS:")
    print("-" * 30)
    
    try:
        with sqlite3.connect("events.db") as conn:
            now = datetime.utcnow()
            next_24h = now + timedelta(hours=24)
            
            events = conn.execute("""
                SELECT id, type, symbol, t0_iso, enabled
                FROM events 
                WHERE datetime(t0_iso) BETWEEN datetime(?) AND datetime(?)
                AND enabled = 1
                ORDER BY t0_iso ASC
            """, (now.isoformat(), next_24h.isoformat())).fetchall()
            
            if events:
                print(f"📊 Eventos próximos (24h): {len(events)}")
                for event in events:
                    event_time = datetime.fromisoformat(event[3])
                    time_until = event_time - now
                    print(f"  - {event[0]}: {event[1]} ({event[2]}) en {time_until}")
            else:
                print("📊 No hay eventos próximos en las próximas 24h")
                
    except Exception as e:
        print(f"❌ Error verificando eventos: {e}")

def check_system_status():
    """Verifica estado del sistema"""
    print("\n🖥️ VERIFICANDO ESTADO DEL SISTEMA:")
    print("-" * 30)
    
    # Verificar archivos críticos
    critical_files = [
        "events.db",
        "p1/event_scheduler.py",
        "app.py",
        ".env"
    ]
    
    for file in critical_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: No encontrado")
    
    # Verificar directorios
    critical_dirs = [
        "logs",
        "p1",
        "scripts",
        "tests"
    ]
    
    for dir in critical_dirs:
        if os.path.isdir(dir):
            files_count = len(os.listdir(dir))
            print(f"📁 {dir}/: {files_count} archivos")
        else:
            print(f"❌ {dir}/: No encontrado")

def main():
    """Función principal de monitoreo"""
    print("🎯 EVENTARB BOT - MONITOREO DEL SISTEMA")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    check_database_status()
    check_environment()
    check_upcoming_events()
    check_system_status()
    
    print("\n" + "=" * 50)
    print("✅ Monitoreo completado")

if __name__ == "__main__":
    main()
