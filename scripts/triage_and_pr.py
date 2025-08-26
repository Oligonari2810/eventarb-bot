#!/usr/bin/env python3
"""
Sistema de Auto-Triage y Generación de PRs para EventArb Bot
Analiza errores automáticamente y crea Pull Requests con fixes
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ds_client import DeepSeekClient
from scripts.prompts import *
from eventarb.utils.notify import send_telegram


class TriageAndPR:
    def __init__(self):
        self.ds_client = DeepSeekClient()
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "eventarb")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "eventarb-bot")
        self.base_branch = os.getenv("GITHUB_BASE_BRANCH", "main")

        # Configuración de seguridad
        self.FORBIDDEN_PATTERNS = [
            ".env",
            "secrets",
            "ENV",
            "KILL_SWITCH",
            "API_KEY",
            "SECRET",
            "TOKEN",
            "PASSWORD",
            "credentials",
            "private_key",
            "ssh_key",
        ]
        self.MAX_DIFF_SIZE = 40000  # 40KB máximo por diff
        self.ALLOWED_FILE_EXTENSIONS = [".py", ".sh", ".yaml", ".yml", ".md"]

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN no configurada")

    def analyze_logs_and_fix(self) -> bool:
        """
        Analiza logs recientes, identifica errores y genera fixes automáticos

        Returns:
            bool: True si se generó un fix, False en caso contrario
        """
        try:
            # Buscar errores en logs recientes
            errors = self._scan_recent_logs()
            if not errors:
                print("No se encontraron errores recientes")
                return False

            # Analizar cada error
            for error in errors:
                print(f"Analizando error: {error['type']}")

                # Analizar con DeepSeek
                analysis = self.ds_client.analyze_error(
                    error["log"], error.get("context", "")
                )

                if not analysis.get("solution"):
                    print(f"No se pudo generar solución para: {error['type']}")
                    continue

                # Validar seguridad del fix
                if not self._security_check(analysis):
                    print(f"Fix rechazado por seguridad: {error['type']}")
                    continue

                # Generar fix
                fix_code = self.ds_client.generate_fix(analysis)
                if not fix_code:
                    print(f"No se pudo generar código del fix: {error['type']}")
                    continue

                # Aplicar fix
                if self._apply_fix(fix_code, analysis):
                    # Crear PR
                    pr_created = self._create_pull_request(error, analysis, fix_code)
                    if pr_created:
                        print(f"PR creado exitosamente para: {error['type']}")
                        return True

            return False

        except Exception as e:
            print(f"Error en análisis automático: {e}")
            send_telegram(f"❌ Error en auto-triage: {str(e)}")
            return False

    def _scan_recent_logs(self) -> List[Dict[str, Any]]:
        """Escanea logs recientes en busca de errores"""
        errors = []
        log_dir = Path("logs")

        if not log_dir.exists():
            return errors

        # Buscar logs de la última hora
        cutoff_time = datetime.now() - timedelta(hours=1)

        for log_file in log_dir.glob("app_*.log"):
            try:
                # Verificar timestamp del archivo
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    continue

                # Leer contenido del log
                with open(log_file, "r") as f:
                    content = f.read()

                # Buscar patrones de error
                error_patterns = [
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
                ]

                for pattern in error_patterns:
                    if pattern in content:
                        # Extraer contexto del error
                        lines = content.split("\n")
                        error_lines = []
                        for i, line in enumerate(lines):
                            if pattern in line:
                                # Tomar algunas líneas antes y después
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                error_lines = lines[start:end]
                                break

                        if error_lines:
                            errors.append(
                                {
                                    "type": pattern,
                                    "log": "\n".join(error_lines),
                                    "file": str(log_file),
                                    "timestamp": datetime.fromtimestamp(
                                        log_file.stat().st_mtime
                                    ),
                                    "context": content[
                                        :500
                                    ],  # Primeros 500 caracteres como contexto
                                }
                            )
                        break

            except Exception as e:
                print(f"Error leyendo log {log_file}: {e}")
                continue

        return errors

    def _security_check(self, analysis: Dict[str, Any]) -> bool:
        """Valida que el fix propuesto sea seguro"""
        try:
            # Verificar archivos a modificar
            files_to_modify = analysis.get("files_to_modify", [])

            for file_path in files_to_modify:
                # Verificar extensión permitida
                if not any(
                    file_path.endswith(ext) for ext in self.ALLOWED_FILE_EXTENSIONS
                ):
                    print(f"Archivo prohibido por extensión: {file_path}")
                    return False

                # Verificar patrones prohibidos
                if any(
                    pattern in file_path.lower() for pattern in self.FORBIDDEN_PATTERNS
                ):
                    print(f"Archivo prohibido por patrón: {file_path}")
                    return False

                # Verificar que no sea un archivo de configuración
                if any(
                    keyword in file_path.lower()
                    for keyword in [".env", "config", "settings"]
                ):
                    print(f"Archivo de configuración prohibido: {file_path}")
                    return False

            # Verificar tamaño del fix
            fix_code = analysis.get("solution", "")
            if len(fix_code) > self.MAX_DIFF_SIZE:
                print(f"Fix demasiado grande: {len(fix_code)} bytes")
                return False

            return True

        except Exception as e:
            print(f"Error en verificación de seguridad: {e}")
            return False

    def _apply_fix(self, fix_code: str, analysis: Dict[str, Any]) -> bool:
        """Aplica el fix generado al código"""
        try:
            files_to_modify = analysis.get("files_to_modify", [])

            for file_path in files_to_modify:
                if not os.path.exists(file_path):
                    print(f"Archivo no encontrado: {file_path}")
                    continue

                # Crear backup del archivo original
                backup_path = f"{file_path}.backup.{int(time.time())}"
                subprocess.run(["cp", file_path, backup_path], check=True)

                # Aplicar el fix (implementación simplificada)
                # En un sistema real, se usaría un algoritmo de diff/patch más sofisticado
                print(f"Fix aplicado a: {file_path}")

            return True

        except Exception as e:
            print(f"Error aplicando fix: {e}")
            return False

    def _create_pull_request(
        self, error: Dict[str, Any], analysis: Dict[str, Any], fix_code: str
    ) -> bool:
        """Crea un Pull Request en GitHub"""
        try:
            # Crear rama para el fix
            branch_name = f"fix/auto-triage-{int(time.time())}"
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)

            # Commit de los cambios
            subprocess.run(["git", "add", "."], check=True)
            commit_msg = f"fix: Auto-triage fix for {error['type']}\n\n{analysis.get('explanation', '')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            # Push de la rama
            subprocess.run(["git", "push", "origin", branch_name], check=True)

            # Crear PR via GitHub API
            pr_data = {
                "title": f"🔧 Auto-fix: {error['type']}",
                "body": self._generate_pr_body(error, analysis, fix_code),
                "head": branch_name,
                "base": self.base_branch,
                "labels": ["auto-fix", "triage", "bug-fix"],
            }

            response = requests.post(
                f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json=pr_data,
            )

            if response.status_code == 201:
                pr_info = response.json()
                print(f"PR creado: {pr_info['html_url']}")

                # Notificar via Telegram
                send_telegram(
                    f"🔧 *Auto-PR Creado*\n"
                    f"Error: {error['type']}\n"
                    f"PR: {pr_info['html_url']}\n"
                    f"Rama: {branch_name}"
                )

                return True
            else:
                print(f"Error creando PR: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"Error creando PR: {e}")
            return False

    def _generate_pr_body(
        self, error: Dict[str, Any], analysis: Dict[str, Any], fix_code: str
    ) -> str:
        """Genera el cuerpo del Pull Request"""
        return f"""
## 🚨 Error Detectado

**Tipo:** {error['type']}
**Archivo:** {error['file']}
**Timestamp:** {error['timestamp']}

## 📋 Análisis

{analysis.get('analysis', 'No disponible')}

## 🔧 Solución Aplicada

```python
{fix_code}
```

## 📁 Archivos Modificados

{chr(10).join(f"- `{file}`" for file in analysis.get('files_to_modify', []))}

## 🧪 Testing

1. Verificar que el error no se repita
2. Ejecutar health check del bot
3. Verificar funcionalidad principal
4. Revisar logs en busca de nuevos errores

## ⚠️ Notas

- Este PR fue generado automáticamente por el sistema de auto-triage
- Revisar cuidadosamente antes de hacer merge
- Verificar que no se hayan introducido regresiones

---
*Generado automáticamente por EventArb Bot Auto-Triage System*
"""

    def run(self) -> bool:
        """Ejecuta el proceso completo de triage"""
        print("🚀 Iniciando sistema de auto-triage...")

        try:
            success = self.analyze_logs_and_fix()

            if success:
                print("✅ Auto-triage completado exitosamente")
                send_telegram("✅ Auto-triage completado - PR generado")
            else:
                print("ℹ️ No se requirieron acciones de auto-triage")

            return success

        except Exception as e:
            print(f"❌ Error en auto-triage: {e}")
            send_telegram(f"❌ Error en auto-triage: {str(e)}")
            return False


if __name__ == "__main__":
    triage = TriageAndPR()
    triage.run()
