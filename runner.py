#!/usr/bin/env python3
"""
EventArb Bot Runner - Versión optimizada con logging robusto
Resuelve el error crítico de 'Bad file descriptor'
"""

import logging
import logging.handlers
import os
import signal
import sys
import time
import subprocess
import threading

# Configurar logging robusto
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger(name, log_file):
    """Configura logger robusto con rotación automática"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Evitar handlers duplicados
    if logger.handlers:
        return logger

    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=5,
        delay=True,
        encoding="utf-8",  # 5MB
    )

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Configurar logger principal
logger = setup_logger("bot_runner", "logs/runner.log")


def start_event_scheduler():
    """Inicia el Event Scheduler directamente (NO en thread separado)"""
    try:
        from p1.event_scheduler import EventScheduler
        
        # Crear scheduler directamente
        scheduler = EventScheduler(db_path="trades.db", check_interval=60)  # Verificar cada minuto
        
        # Cargar eventos iniciales
        events = scheduler.load_upcoming_events()
        logger.info(f"✅ Event Scheduler creado - {len(events)} eventos cargados")
        
        # Programar eventos iniciales
        for event in events:
            scheduler.schedule_event(event)
        
        logger.info(f"✅ Event Scheduler iniciado directamente - {len(scheduler.active_timers)} timers activos")
        return scheduler, None  # No thread separado
        
    except ImportError as e:
        logger.warning(f"⚠️  No se pudo importar Event Scheduler: {e}")
        return None, None
    except Exception as e:
        logger.error(f"❌ Error iniciando Event Scheduler: {e}")
        return None, None


class BotRunner:
    """Runner principal del bot con manejo robusto de procesos"""

    def __init__(self):
        self.running = True
        self.cycle_count = 0
        self.event_scheduler = None
        self.scheduler_thread = None

        # Configurar señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("🚀 EventArb Bot Runner iniciado")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Iniciar Event Scheduler
        self.event_scheduler, self.scheduler_thread = start_event_scheduler()

    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación de forma segura"""
        logger.info(f"📴 Señal recibida: {signum}")
        
        # Detener Event Scheduler
        if self.event_scheduler:
            self.event_scheduler.stop()
            logger.info("🛑 Event Scheduler detenido")
        
        self.running = False

    def run_bot_cycle(self):
        """Ejecuta un ciclo del bot usando subprocesos separados"""
        self.cycle_count += 1
        
        # EJECUTAR EVENT SCHEDULER DIRECTAMENTE
        if self.event_scheduler:
            try:
                # Ejecutar una iteración del scheduler
                self._run_scheduler_iteration()
            except Exception as e:
                logger.error(f"❌ Error en Event Scheduler: {e}")
        
        timestamp = time.strftime("%F %T")
        log_file = f"logs/app_{timestamp}.log"
        
        try:
            # Configurar entorno
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Buscar Python del entorno virtual
            python_executable = os.path.join("venv", "bin", "python")
            
            if not os.path.exists(python_executable):
                # Fallback al Python del sistema
                python_executable = sys.executable
                logger.warning("⚠️  Usando Python del sistema (entorno virtual no encontrado)")
            else:
                logger.info(f"✅ Usando Python del entorno virtual: {python_executable}")
            
            # Ejecutar como módulo Python para evitar problemas de streams
            try:
                result = subprocess.run(
                    [python_executable, '-u', 'app.py'],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=15,  # Timeout de 15 segundos
                    check=False  # No fallar si app.py retorna código de error
                )
                
                # Capturar logs
                stdout_lines = result.stdout.strip().split('\n') if result.stdout else []
                stderr_lines = result.stderr.strip().split('\n') if result.stderr else []
                
                # Log stdout
                for line in stdout_lines:
                    if line.strip():
                        logger.info(f"app.py: {line.strip()}")
                
                # Log stderr
                for line in stderr_lines:
                    if line.strip():
                        logger.error(f"app.py ERROR: {line.strip()}")
                
                exit_code = result.returncode
                
            except subprocess.TimeoutExpired:
                logger.error("❌ app.py timeout después de 15 segundos")
                exit_code = -1
                stdout_lines = ["TIMEOUT: app.py no respondió en 15 segundos"]
                stderr_lines = ["TIMEOUT: app.py no respondió en 15 segundos"]
            except subprocess.SubprocessError as e:
                logger.error(f"❌ Error de subproceso: {e}")
                exit_code = -1
                stdout_lines = [f"SUBPROCESS ERROR: {e}"]
                stderr_lines = [f"SUBPROCESS ERROR: {e}"]
            except Exception as e:
                logger.error(f"❌ Error inesperado ejecutando app.py: {e}")
                exit_code = -1
                stdout_lines = [f"UNEXPECTED ERROR: {e}"]
                stderr_lines = [f"UNEXPECTED ERROR: {e}"]
            
            # Escribir log completo
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Iniciando app.py...\n")
                if stdout_lines:
                    f.write("\n".join([f"STDOUT: {line}" for line in stdout_lines]) + "\n")
                if stderr_lines:
                    f.write("\n".join([f"STDERR: {line}" for line in stderr_lines]) + "\n")
                f.write(f"[{time.strftime('%F %T')}] app.py terminó con código: {exit_code}\n")

            logger.info(
                f"✅ Ciclo {self.cycle_count} completado - Exit code: {exit_code}"
            )

            if exit_code == 0:
                logger.info("🎯 Bot terminó normalmente (límites diarios alcanzados)")
            else:
                logger.warning(f"⚠️ Bot terminó con error: {exit_code}")

        except Exception as e:
            logger.error(f"❌ Error en ciclo {self.cycle_count}: {e}")
            # Crear log de error
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"[{timestamp}] ERROR: {e}\n")

    def _run_scheduler_iteration(self):
        """Ejecuta una iteración del Event Scheduler"""
        try:
            # Cargar eventos próximos
            events = self.event_scheduler.load_upcoming_events()
            
            # Programar eventos nuevos
            for event in events:
                event_id = event[0]
                if event_id not in self.event_scheduler.active_timers:
                    self.event_scheduler.schedule_event(event)
                    logger.info(f"🎯 Evento programado: {event_id}")
            
            # Verificar timers activos
            active_count = len(self.event_scheduler.active_timers)
            if active_count > 0:
                logger.info(f"⏰ Timers activos: {active_count}")
                
        except Exception as e:
            logger.error(f"❌ Error en iteración del scheduler: {e}")

    def run(self):
        """Bucle principal del runner"""
        logger.info("🔄 Iniciando bucle principal del bot")

        while self.running:
            try:
                self.run_bot_cycle()

                if not self.running:
                    break

                # Pausa entre ciclos
                logger.info("⏳ Pausa de 5 segundos...")
                time.sleep(5)

            except KeyboardInterrupt:
                logger.info("🛑 Interrupción del usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error crítico en runner: {e}")
                time.sleep(10)  # Pausa más larga en caso de error

        logger.info("🏁 Bot Runner terminado")


def main():
    """Función principal"""
    try:
        runner = BotRunner()
        runner.run()
    except Exception as e:
        logger.error(f"❌ Error fatal en main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
