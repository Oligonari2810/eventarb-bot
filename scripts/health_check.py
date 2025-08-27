#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path para importar eventarb
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eventarb.utils.notify import send_telegram

LOG_DIR = "logs"
STALE_SECONDS = 90  # 1.5 minutos sin logs → alerta


def is_runner_alive():
    """Verifica si run_forever.sh está ejecutándose"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "run_forever.sh"], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def latest_log_mtime():
    """Obtiene timestamp del log más reciente"""
    log_path = Path(LOG_DIR)
    if not log_path.exists():
        return 0

    log_files = list(log_path.glob("app_*.log"))
    if not log_files:
        return 0

    latest_file = max(log_files, key=lambda x: x.stat().st_mtime)
    return latest_file.stat().st_mtime


def main():
    """Verificación principal de salud"""
    # Verificar proceso
    if not is_runner_alive():
        send_telegram("🔴 *EventArb Caído*\nRunner no encontrado en procesos")
        sys.exit(1)

    # Verificar frescura de logs
    last_log_time = latest_log_mtime()
    current_time = time.time()

    if last_log_time == 0:
        send_telegram("🟠 *EventArb Sin Logs*\nNo se encuentran archivos de log")
        sys.exit(2)

    if current_time - last_log_time > STALE_SECONDS:
        send_telegram("🟠 *EventArb Inactivo*\nSin logs nuevos en 90 segundos")
        sys.exit(3)

    # Todo OK
    sys.exit(0)


if __name__ == "__main__":
    main()
