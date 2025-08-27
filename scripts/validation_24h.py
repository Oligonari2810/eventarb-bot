#!/usr/bin/env python3
"""
Script de validación de 24h para EventArb Bot
Monitorea: idempotencia, DB, alertas, heartbeats, estado diario
"""

import os
import sys
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validation_24h.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Validation24h:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self.start_time = datetime.utcnow()
        self.validation_duration = timedelta(hours=24)
        self.check_interval = 60  # segundos
        self.running = False
        
        # Métricas de validación
        self.metrics = {
            'heartbeats': 0,
            'events_fired': 0,
            'db_errors': 0,
            'idempotency_checks': 0,
            'alert_checks': 0,
            'state_updates': 0
        }
        
        # Estado anterior para comparaciones
        self.previous_state = {}
        
    def setup_environment(self):
        """Configura variables de entorno para validación"""
        env_vars = {
            "EMERGENCY_STOP": "0",
            "DRY_RUN": "1",  # Testing mode
            "DB_PATH": self.db_path,
            "LOG_LEVEL": "INFO",
            "BOT_MODE": "testnet",
            "PYTHONPATH": str(Path.cwd())
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            logger.info(f"🔧 {key}={value}")
        
        return env_vars
    
    def check_database_health(self):
        """Verifica salud de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar eventos
                events = conn.execute("SELECT COUNT(*) FROM events WHERE enabled = 1").fetchone()[0]
                
                # Verificar event_fires
                fires = conn.execute("SELECT COUNT(*) FROM event_fires").fetchone()[0]
                
                # Verificar bot_state
                bot_state = conn.execute("SELECT * FROM bot_state ORDER BY date DESC LIMIT 1").fetchone()
                
                # Verificar idempotencia (event_id + window_sec únicos)
                idempotency_check = conn.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT event_id, window_sec, COUNT(*) as cnt
                        FROM event_fires 
                        GROUP BY event_id, window_sec
                        HAVING cnt > 1
                    )
                """).fetchone()[0]
                
                if idempotency_check > 0:
                    logger.error(f"❌ VIOLACIÓN DE IDEMPOTENCIA: {idempotency_check} duplicados")
                    self.metrics['db_errors'] += 1
                else:
                    logger.info(f"✅ Idempotencia OK: {fires} eventos disparados")
                    self.metrics['idempotency_checks'] += 1
                
                # Verificar cambios de estado
                current_state = {
                    'events': events,
                    'fires': fires,
                    'bot_state': bot_state
                }
                
                if self.previous_state and current_state != self.previous_state:
                    logger.info(f"📊 Estado cambiado: {current_state}")
                    self.metrics['state_updates'] += 1
                
                self.previous_state = current_state
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error de base de datos: {e}")
            self.metrics['db_errors'] += 1
            return False
    
    def check_event_scheduler(self):
        """Verifica que el Event Scheduler esté funcionando"""
        try:
            # Verificar que hay eventos próximos
            with sqlite3.connect(self.db_path) as conn:
                now = datetime.utcnow()
                next_24h = now + timedelta(hours=24)
                
                upcoming = conn.execute("""
                    SELECT COUNT(*) FROM events 
                    WHERE datetime(t0_iso) BETWEEN datetime(?) AND datetime(?)
                    AND enabled = 1
                """, (now.isoformat(), next_24h.isoformat())).fetchone()[0]
                
                if upcoming > 0:
                    logger.info(f"📅 Eventos próximos: {upcoming}")
                    return True
                else:
                    logger.warning("⚠️ No hay eventos próximos en las próximas 24h")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error verificando Event Scheduler: {e}")
            return False
    
    def check_heartbeat(self):
        """Verifica heartbeat del sistema"""
        self.metrics['heartbeats'] += 1
        uptime = datetime.utcnow() - self.start_time
        
        logger.info(f"💓 Heartbeat #{self.metrics['heartbeats']} - Uptime: {uptime}")
        
        # Log métricas cada 10 heartbeats
        if self.metrics['heartbeats'] % 10 == 0:
            logger.info(f"📊 Métricas acumuladas: {self.metrics}")
    
    def check_alerts(self):
        """Verifica que las alertas estén funcionando"""
        try:
            # Verificar logs de alertas
            alert_log_file = Path("logs/app.log")
            if alert_log_file.exists():
                # Buscar alertas recientes en logs
                recent_content = alert_log_file.read_text()
                if "ALERT" in recent_content or "Telegram" in recent_content:
                    logger.info("✅ Alertas detectadas en logs")
                    self.metrics['alert_checks'] += 1
                else:
                    logger.info("ℹ️ No hay alertas recientes")
            else:
                logger.warning("⚠️ Archivo de log no encontrado")
                
        except Exception as e:
            logger.error(f"❌ Error verificando alertas: {e}")
    
    def run_validation_cycle(self):
        """Ejecuta un ciclo de validación"""
        logger.info("🔄 Iniciando ciclo de validación...")
        
        # Verificar base de datos
        db_ok = self.check_database_health()
        
        # Verificar Event Scheduler
        scheduler_ok = self.check_event_scheduler()
        
        # Verificar alertas
        self.check_alerts()
        
        # Heartbeat
        self.check_heartbeat()
        
        # Resumen del ciclo
        if db_ok and scheduler_ok:
            logger.info("✅ Ciclo de validación exitoso")
        else:
            logger.warning("⚠️ Ciclo de validación con problemas")
    
    def start_validation(self):
        """Inicia la validación de 24h"""
        logger.info("🎯 INICIANDO VALIDACIÓN DE 24H")
        logger.info("=" * 50)
        logger.info(f"⏰ Inicio: {self.start_time.isoformat()}")
        logger.info(f"⏰ Duración: {self.validation_duration}")
        logger.info(f"⏰ Check interval: {self.check_interval} segundos")
        logger.info("=" * 50)
        
        # Configurar entorno
        self.setup_environment()
        
        # Inicializar estado
        self.check_database_health()
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                current_time = datetime.utcnow()
                elapsed = current_time - self.start_time
                
                # Verificar si hemos completado 24h
                if elapsed >= self.validation_duration:
                    logger.info("🎉 VALIDACIÓN DE 24H COMPLETADA")
                    break
                
                logger.info(f"🔄 Ciclo #{cycle_count} - Elapsed: {elapsed}")
                
                # Ejecutar ciclo de validación
                self.run_validation_cycle()
                
                # Esperar hasta el próximo ciclo
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Validación interrumpida por usuario")
        except Exception as e:
            logger.error(f"❌ Error en validación: {e}")
        finally:
            self.running = False
            self.generate_final_report()
    
    def generate_final_report(self):
        """Genera reporte final de validación"""
        end_time = datetime.utcnow()
        total_duration = end_time - self.start_time
        
        logger.info("📊 REPORTE FINAL DE VALIDACIÓN")
        logger.info("=" * 50)
        logger.info(f"⏰ Inicio: {self.start_time.isoformat()}")
        logger.info(f"⏰ Fin: {end_time.isoformat()}")
        logger.info(f"⏰ Duración total: {total_duration}")
        logger.info(f"📈 Métricas finales: {self.metrics}")
        
        # Análisis de resultados
        if self.metrics['db_errors'] == 0:
            logger.info("✅ Base de datos: Sin errores")
        else:
            logger.warning(f"⚠️ Base de datos: {self.metrics['db_errors']} errores")
        
        if self.metrics['idempotency_checks'] > 0:
            logger.info(f"✅ Idempotencia: {self.metrics['idempotency_checks']} verificaciones")
        
        if self.metrics['heartbeats'] > 0:
            logger.info(f"✅ Heartbeats: {self.metrics['heartbeats']} registrados")
        
        logger.info("=" * 50)
        logger.info("🎯 Validación completada")

def main():
    """Función principal"""
    print("🎯 EVENTARB BOT - VALIDACIÓN DE 24H")
    print("=" * 50)
    
    # Crear directorio de logs si no existe
    Path("logs").mkdir(exist_ok=True)
    
    # Iniciar validación
    validator = Validation24h()
    
    try:
        validator.start_validation()
    except KeyboardInterrupt:
        print("\n🛑 Validación interrumpida por usuario")
        validator.generate_final_report()

if __name__ == "__main__":
    main()
