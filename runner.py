#!/usr/bin/env python3
"""
EventArb Bot Runner - Versión optimizada con logging robusto
Resuelve el error crítico de 'Bad file descriptor'
"""

import logging
import logging.handlers
import os
import sys
import time
import signal
import subprocess

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
        log_file, maxBytes=5_000_000, backupCount=5, delay=True, encoding="utf-8"  # 5MB
    )

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


# Configurar logger principal
logger = setup_logger("bot_runner", "logs/runner.log")


class BotRunner:
    """Runner principal del bot con manejo robusto de procesos"""

    def __init__(self):
        self.process = None
        self.running = True
        self.cycle_count = 0

        # Configurar señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("🚀 EventArb Bot Runner iniciado")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")

    def _signal_handler(self, signum, frame):
        """Maneja señales de terminación de forma segura"""
        logger.info(f"📴 Señal recibida: {signum}")
        self.running = False
        if self.process:
            logger.info("🔄 Terminando proceso del bot...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Proceso no terminó, forzando...")
                self.process.kill()

    def run_bot_cycle(self):
        """Ejecuta un ciclo del bot"""
        self.cycle_count += 1
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        log_file = f"logs/app_{timestamp}.log"

        logger.info(f"🔄 Ciclo {self.cycle_count}: Iniciando app.py")

        try:
            # Ejecutar app.py con logging robusto
            self.process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Capturar output de forma segura
            stdout, stderr = self.process.communicate()
            exit_code = self.process.returncode

            # Escribir logs de forma segura
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Iniciando app.py...\n")
                if stdout:
                    f.write(stdout)
                if stderr:
                    f.write(f"\n--- ERRORES ---\n{stderr}")
                f.write(
                    f"\n[{time.strftime('%F %T')}] app.py terminó con código: {exit_code}\n"
                )

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
