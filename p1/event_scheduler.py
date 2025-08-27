#!/usr/bin/env python3
"""
Event Scheduler para EventArb Bot
Programa y dispara eventos económicos automáticamente
"""

import sqlite3
import time
import logging
import threading
from datetime import datetime, timedelta
from threading import Timer

logger = logging.getLogger(__name__)


class EventScheduler:
    def __init__(self, db_path="trades.db", check_interval=300):
        self.db_path = db_path
        self.check_interval = check_interval
        self.active_timers = {}
        self.running = False
        self.scheduler_thread = None
        
    def load_upcoming_events(self):
        """Carga eventos de las próximas 24 horas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.utcnow()
            next_24h = now + timedelta(hours=24)
            
            cursor.execute("""
                SELECT id, t0_iso, symbol, type, consensus 
                FROM events 
                WHERE datetime(t0_iso) BETWEEN datetime(?) AND datetime(?)
                AND enabled = 1
                ORDER BY t0_iso ASC
            """, (now.isoformat(), next_24h.isoformat()))
            
            events = cursor.fetchall()
            conn.close()
            
            logger.info(f"Loaded {len(events)} upcoming events")
            return events
            
        except Exception as e:
            logger.error(f"Error loading events: {e}")
            return []
    
    def schedule_event(self, event):
        """Programa un evento para su ejecución"""
        event_id, t0_iso, symbol, event_type, consensus = event
        
        try:
            # Parsear timestamp ISO
            if t0_iso.endswith('Z'):
                t0_iso = t0_iso[:-1] + '+00:00'
            
            event_time = datetime.fromisoformat(t0_iso)
            now = datetime.utcnow()
            delay = (event_time - now).total_seconds()
            
            if delay < 0:
                logger.warning(f"Event {event_id} is in the past (delay: {delay:.0f}s)")
                return
            
            # Cancelar timer existente si hay uno
            if event_id in self.active_timers:
                self.active_timers[event_id].cancel()
                logger.info(f"Cancelled existing timer for event {event_id}")
            
            # Programar nuevo timer
            timer = Timer(delay, self.trigger_event, [event])
            timer.start()
            self.active_timers[event_id] = timer
            
            logger.info(f"Scheduled event {event_id} ({symbol} {event_type}) for {event_time} (delay: {delay:.0f}s)")
            
        except Exception as e:
            logger.error(f"Error scheduling event {event_id}: {e}")
    
    def trigger_event(self, event):
        """Dispara el evento llamando a on_event"""
        event_id, t0_iso, symbol, event_type, consensus = event
        
        try:
            # Calcular window_sec para idempotencia (ventana de 5 minutos)
            now = datetime.utcnow()
            window_sec = (now.hour * 3600 + now.minute * 60) // 300 * 300
            
            # Registrar que se disparó con window_sec para idempotencia
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT OR IGNORE INTO event_fires (event_id, window_sec, fired_at) VALUES (?, ?, ?)",
                (event_id, window_sec, now.isoformat())
            )
            conn.commit()
            conn.close()
            
            # Llamar a la función del bot
            try:
                from app import on_event
                event_data = {
                    'id': event_id,
                    't0_iso': t0_iso,
                    'symbol': symbol,
                    'type': event_type,
                    'consensus': consensus
                }
                on_event(event_data)
                
            except ImportError:
                logger.warning("app.on_event not found, logging event only")
            except Exception as e:
                logger.error(f"Error calling on_event: {e}")
            
            # Limpiar timer
            if event_id in self.active_timers:
                del self.active_timers[event_id]
            
            logger.info(f"🎯 EVENT_FIRE id={event_id} symbol={symbol} type={event_type}")
            
        except Exception as e:
            logger.error(f"Error triggering event {event_id}: {e}")
    
    def add_test_event(self, minutes_from_now=2):
        """Agrega un evento de prueba para testing"""
        try:
            event_time = datetime.utcnow() + timedelta(minutes=minutes_from_now)
            event_id = f"test_{int(time.time())}"
            
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO events (id, t0_iso, symbol, type, consensus, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_id, event_time.isoformat(), "BTCUSDT", "TEST", "{}", 1))
            conn.commit()
            conn.close()
            
            logger.info(f"Added test event {event_id} for {event_time}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error adding test event: {e}")
            return None
    
    def get_scheduled_events(self):
        """Retorna lista de eventos programados actualmente"""
        events = []
        for event_id, timer in self.active_timers.items():
            if timer.is_alive():
                events.append(event_id)
        return events
    
    def stop(self):
        """Detiene el scheduler"""
        self.running = False
        
        # Cancelar todos los timers activos
        for event_id, timer in self.active_timers.items():
            timer.cancel()
            logger.info(f"Cancelled timer for event {event_id}")
        
        self.active_timers.clear()
        logger.info("Event Scheduler stopped")
    
    def run(self):
        """Loop principal del scheduler"""
        logger.info("🚀 Starting Event Scheduler")
        logger.info(f"🔧 DEBUG: check_interval = {self.check_interval} segundos")
        logger.info(f"🔧 DEBUG: db_path = {self.db_path}")
        self.running = True
        
        loop_count = 0
        while self.running:
            loop_count += 1
            try:
                logger.info(f"🔄 DEBUG: Loop #{loop_count} - Cargando eventos próximos...")
                
                # Cargar eventos próximos
                events = self.load_upcoming_events()
                logger.info(f"🔧 DEBUG: Encontrados {len(events)} eventos próximos")
                
                # Programar eventos nuevos
                for event in events:
                    event_id = event[0]
                    if event_id not in self.active_timers:
                        logger.info(f"🔧 DEBUG: Programando evento nuevo: {event_id}")
                        self.schedule_event(event)
                    else:
                        logger.info(f"🔧 DEBUG: Evento ya programado: {event_id}")
                
                # Log estado actual
                active_count = len(self.active_timers)
                logger.info(f"🔧 DEBUG: Timers activos: {active_count}")
                if active_count > 0:
                    logger.info(f"Active timers: {active_count}")
                
                # Esperar hasta la próxima verificación
                logger.info(f"🔧 DEBUG: Esperando {self.check_interval} segundos hasta próxima verificación...")
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                logger.error(f"🔧 DEBUG: Error en loop #{loop_count}: {e}")
                time.sleep(60)  # Pausa más corta en caso de error
        
        logger.info("Event Scheduler main loop ended")


def start_event_scheduler(db_path="trades.db", check_interval=300):
    """Función helper para iniciar el scheduler en un thread separado"""
    scheduler = EventScheduler(db_path, check_interval)
    scheduler_thread = threading.Thread(target=scheduler.run, daemon=False)  # CAMBIADO A False
    scheduler_thread.start()
    
    logger.info("Event Scheduler started in background thread")
    return scheduler, scheduler_thread


if __name__ == "__main__":
    # Test del scheduler
    logging.basicConfig(level=logging.INFO)
    
    scheduler = EventScheduler()
    
    # Agregar evento de prueba
    test_event_id = scheduler.add_test_event(minutes_from_now=1)
    
    if test_event_id:
        print(f"Test event added: {test_event_id}")
        print("Starting scheduler for 2 minutes...")
        
        try:
            scheduler.run()
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop()
    else:
        print("Failed to add test event")
