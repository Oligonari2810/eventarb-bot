#!/usr/bin/env python3
"""
Log Sentry para EventArb Bot
Monitorea logs en tiempo real y dispara el sistema de auto-triage cuando detecta errores
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Set

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eventarb.utils.notify import send_telegram


class LogSentry:
    def __init__(self):
        self.log_dir = Path("logs")
        self.monitored_files: Set[str] = set()
        self.error_patterns = [
            "ERROR:",
            "Exception:",
            "Traceback:",
            "Fatal error:",
            "NameError:",
            "TypeError:",
            "ValueError:",
            "AttributeError:",
            "ImportError:",
            "ModuleNotFoundError:",
            "FileNotFoundError:",
            "OSError:",
            "RuntimeError:",
            "SystemError:",
        ]
        self.critical_patterns = [
            "Fatal Python error",
            "OSError: [Errno 9]",
            "Bad file descriptor",
            "can't initialize sys standard streams",
            "KILL_SWITCH=1",
        ]

        # Configuración de monitoreo
        self.scan_interval = 30  # segundos
        self.error_threshold = 3  # errores antes de disparar triage
        self.critical_threshold = 1  # errores críticos para disparo inmediato
        self.last_triage_time = 0
        self.triage_cooldown = 300  # 5 minutos entre triages

        # Contadores de errores
        self.error_counts: Dict[str, int] = {}
        self.critical_errors: Set[str] = set()

        # Señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Estado del sistema
        self.running = True
        self.triage_process: Optional[subprocess.Popen] = None

    def _signal_handler(self, signum, frame):
        """Maneja señales de shutdown"""
        print(f"\n🛑 Señal recibida: {signum}. Cerrando sentry...")
        self.running = False
        if self.triage_process:
            self.triage_process.terminate()

    def start_monitoring(self):
        """Inicia el monitoreo continuo de logs"""
        print("🚀 Iniciando Log Sentry...")
        print(f"📁 Monitoreando directorio: {self.log_dir.absolute()}")
        print(f"⏱️ Intervalo de escaneo: {self.scan_interval} segundos")
        print(f"🔍 Patrones de error: {len(self.error_patterns)}")
        print(f"🚨 Patrones críticos: {len(self.critical_patterns)}")

        send_telegram("🟢 Log Sentry iniciado - Monitoreando logs del bot")

        try:
            while self.running:
                self._scan_logs()
                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            print("\n🛑 Interrumpido por usuario")
        except Exception as e:
            print(f"❌ Error en monitoreo: {e}")
            send_telegram(f"❌ Error en Log Sentry: {str(e)}")
        finally:
            self._cleanup()

    def _scan_logs(self):
        """Escanea logs en busca de errores"""
        try:
            # Actualizar lista de archivos monitoreados
            self._update_monitored_files()

            # Escanear cada archivo
            for log_file in self.monitored_files:
                self._analyze_log_file(log_file)

            # Verificar si se debe disparar triage
            self._check_triage_trigger()

        except Exception as e:
            print(f"Error en escaneo de logs: {e}")

    def _update_monitored_files(self):
        """Actualiza la lista de archivos de log a monitorear"""
        if not self.log_dir.exists():
            return

        # Buscar archivos de log recientes (últimas 24 horas)
        cutoff_time = datetime.now() - timedelta(hours=24)

        for log_file in self.log_dir.glob("*.log"):
            try:
                # Solo monitorear archivos recientes
                if log_file.stat().st_mtime >= cutoff_time.timestamp():
                    self.monitored_files.add(str(log_file))
                else:
                    # Remover archivos antiguos del monitoreo
                    self.monitored_files.discard(str(log_file))

            except Exception as e:
                print(f"Error verificando archivo {log_file}: {e}")

    def _analyze_log_file(self, log_file_path: str):
        """Analiza un archivo de log específico"""
        try:
            log_file = Path(log_file_path)
            if not log_file.exists():
                self.monitored_files.discard(log_file_path)
                return

            # Leer contenido del archivo
            with open(log_file, "r") as f:
                content = f.read()

            # Buscar patrones de error
            for pattern in self.error_patterns:
                if pattern in content:
                    self._record_error(pattern, log_file_path, content)

            # Buscar patrones críticos
            for pattern in self.critical_patterns:
                if pattern in content:
                    self._record_critical_error(pattern, log_file_path, content)

        except Exception as e:
            print(f"Error analizando archivo {log_file_path}: {e}")

    def _record_error(self, pattern: str, file_path: str, content: str):
        """Registra un error detectado"""
        key = f"{pattern}:{file_path}"

        if key not in self.error_counts:
            self.error_counts[key] = 0

        self.error_counts[key] += 1

        # Log del error
        print(
            f"⚠️ Error detectado: {pattern} en {file_path} (count: {self.error_counts[key]})"
        )

        # Si alcanza el umbral, marcar para triage
        if self.error_counts[key] >= self.error_threshold:
            print(f"🚨 Umbral alcanzado para {pattern} en {file_path}")

    def _record_critical_error(self, pattern: str, file_path: str, content: str):
        """Registra un error crítico"""
        key = f"{pattern}:{file_path}"

        if key not in self.critical_errors:
            self.critical_errors.add(key)
            print(f"🚨 ERROR CRÍTICO: {pattern} en {file_path}")

            # Notificar inmediatamente
            send_telegram(
                f"🚨 *ERROR CRÍTICO DETECTADO*\n"
                f"Patrón: {pattern}\n"
                f"Archivo: {file_path}\n"
                f"Timestamp: {datetime.now().isoformat()}"
            )

    def _check_triage_trigger(self):
        """Verifica si se debe disparar el auto-triage"""
        current_time = time.time()

        # Verificar cooldown
        if current_time - self.last_triage_time < self.triage_cooldown:
            return

        # Verificar si hay errores que requieren triage
        should_triage = False
        triage_reason = ""

        # Errores que alcanzaron umbral
        for key, count in self.error_counts.items():
            if count >= self.error_threshold:
                should_triage = True
                triage_reason = f"Umbral de errores alcanzado: {key}"
                break

        # Errores críticos
        if self.critical_errors:
            should_triage = True
            triage_reason = f"Errores críticos detectados: {len(self.critical_errors)}"

        if should_triage:
            print(f"🚀 Disparando auto-triage: {triage_reason}")
            self._trigger_triage(triage_reason)

    def _trigger_triage(self, reason: str):
        """Dispara el proceso de auto-triage"""
        try:
            current_time = time.time()

            # Verificar que no haya un proceso de triage ejecutándose
            if self.triage_process and self.triage_process.poll() is None:
                print("⚠️ Proceso de triage ya en ejecución, saltando...")
                return

            print(f"🔧 Iniciando auto-triage: {reason}")

            # Notificar inicio del triage
            send_telegram(
                f"🔧 *Auto-Triage Iniciado*\n"
                f"Razón: {reason}\n"
                f"Timestamp: {datetime.now().isoformat()}"
            )

            # Ejecutar triage en background
            self.triage_process = subprocess.Popen(
                [sys.executable, "scripts/triage_and_pr.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
            )

            # Actualizar timestamp
            self.last_triage_time = current_time

            # Resetear contadores
            self.error_counts.clear()
            self.critical_errors.clear()

            print("✅ Auto-triage iniciado exitosamente")

        except Exception as e:
            print(f"❌ Error iniciando auto-triage: {e}")
            send_telegram(f"❌ Error iniciando auto-triage: {str(e)}")

    def _cleanup(self):
        """Limpia recursos antes de cerrar"""
        print("🧹 Limpiando recursos...")

        if self.triage_process:
            try:
                self.triage_process.terminate()
                self.triage_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.triage_process.kill()

        send_telegram("🔴 Log Sentry detenido")
        print("✅ Limpieza completada")

    def get_status(self) -> Dict:
        """Retorna el estado actual del sentry"""
        return {
            "running": self.running,
            "monitored_files": len(self.monitored_files),
            "error_counts": len(self.error_counts),
            "critical_errors": len(self.critical_errors),
            "last_triage": self.last_triage_time,
            "triage_cooldown": self.triage_cooldown,
        }


def main():
    """Función principal"""
    try:
        sentry = LogSentry()
        sentry.start_monitoring()
    except Exception as e:
        print(f"❌ Error fatal en Log Sentry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
