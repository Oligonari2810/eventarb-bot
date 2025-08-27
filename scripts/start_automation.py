#!/usr/bin/env python3
"""
Script de automatización completa para EventArb Bot
Inicia Event Scheduler y app.py en modo automático
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

# Configuración
DB_PATH = "events.db"
CHECK_INTERVAL = 30  # segundos
LOG_LEVEL = "INFO"

def setup_environment():
    """Configura variables de entorno para automatización"""
    env_vars = {
        "EMERGENCY_STOP": "0",
        "DRY_RUN": "0",  # Cambiar a "1" para testing
        "DB_PATH": DB_PATH,
        "LOG_LEVEL": LOG_LEVEL,
        "BOT_MODE": "testnet",  # Cambiar a "mainnet" para producción
        "PYTHONPATH": str(Path.cwd())
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"🔧 {key}={value}")
    
    return env_vars

def start_event_scheduler():
    """Inicia el Event Scheduler en un thread separado"""
    print("🚀 Iniciando Event Scheduler...")
    
    try:
        from p1.event_scheduler import EventScheduler
        
        scheduler = EventScheduler(DB_PATH, CHECK_INTERVAL)
        scheduler_thread = threading.Thread(
            target=scheduler.run, 
            daemon=True,
            name="EventScheduler"
        )
        scheduler_thread.start()
        
        print("✅ Event Scheduler iniciado en background")
        return scheduler, scheduler_thread
        
    except Exception as e:
        print(f"❌ Error iniciando Event Scheduler: {e}")
        return None, None

def start_app():
    """Inicia app.py en un thread separado"""
    print("🚀 Iniciando app.py...")
    
    try:
        import app
        
        # Inicializar app
        app.setup_logging()
        app.init_db()
        
        print("✅ app.py inicializado")
        return app
        
    except Exception as e:
        print(f"❌ Error iniciando app.py: {e}")
        return None

def monitor_system(scheduler, app):
    """Monitorea el estado del sistema"""
    print("🔍 Iniciando monitoreo del sistema...")
    
    try:
        while True:
            time.sleep(60)  # Check cada minuto
            
            # Verificar Event Scheduler
            if scheduler and hasattr(scheduler, 'running'):
                print(f"📊 Event Scheduler: {'🟢 Activo' if scheduler.running else '🔴 Inactivo'}")
            
            # Verificar eventos
            try:
                import sqlite3
                with sqlite3.connect(DB_PATH) as conn:
                    events_count = conn.execute("SELECT COUNT(*) FROM events WHERE enabled = 1").fetchone()[0]
                    fires_count = conn.execute("SELECT COUNT(*) FROM event_fires").fetchone()[0]
                    print(f"📈 Eventos: {events_count} activos, {fires_count} disparados")
            except Exception as e:
                print(f"⚠️ Error monitoreando BD: {e}")
                
    except KeyboardInterrupt:
        print("\n🛑 Monitoreo interrumpido")

def signal_handler(signum, frame):
    """Maneja señales de terminación"""
    print(f"\n🛑 Señal {signum} recibida. Deteniendo automatización...")
    sys.exit(0)

def main():
    """Función principal de automatización"""
    print("🎯 EVENTARB BOT - AUTOMATIZACIÓN COMPLETA")
    print("=" * 50)
    
    # Configurar señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configurar entorno
    env_vars = setup_environment()
    print(f"✅ Entorno configurado")
    
    # Iniciar componentes
    scheduler, scheduler_thread = start_event_scheduler()
    app_instance = start_app()
    
    if not scheduler or not app_instance:
        print("❌ Error iniciando componentes. Saliendo...")
        sys.exit(1)
    
    print("🎉 Sistema de automatización iniciado exitosamente!")
    print("📝 Logs disponibles en:")
    print("  - Event Scheduler: console")
    print("  - app.py: logs/app.log")
    print("🔧 Para detener: Ctrl+C")
    
    # Iniciar monitoreo
    try:
        monitor_system(scheduler, app_instance)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo automatización...")
        
        # Limpiar recursos
        if scheduler:
            scheduler.stop()
        print("✅ Automatización detenida")

if __name__ == "__main__":
    main()
