from __future__ import annotations

import time
import requests
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class Rule:
    window: int  # seconds
    threshold: int  # events to trigger
    cooldown: int  # seconds


DEFAULT_RULES = {
    "fatal": None,  # alert inmediatamente
    "error": Rule(window=180, threshold=5, cooldown=300),
    "warning": Rule(window=300, threshold=10, cooldown=600),
}


class AlertManager:
    def __init__(self, rules: Optional[Dict[str, Rule]] = None):
        self.rules = rules or DEFAULT_RULES
        # key = (etype, file), value = dict(count:int, first_ts:float, next_allowed:float)
        self.state: Dict[Tuple[str, str], Dict[str, float]] = {}

    def add(self, etype: str, file: str, now: Optional[float] = None):
        now = now or time.time()
        if etype == "fatal":
            return {
                "emit": True,
                "grouped": False,
                "count": 1,
                "next_allowed": 0,
            }

        rule = self.rules.get(etype)
        if not rule:
            return {"emit": False}

        key = (etype, file)
        s = self.state.get(key, {"count": 0, "first_ts": now, "next_allowed": 0})
        # cooldown activo
        if now < s.get("next_allowed", 0):
            # consumir pero sin emitir
            s["count"] += 1
            self.state[key] = s
            return {"emit": False, "cooldown": True}

        # ventana
        if now - s.get("first_ts", now) > rule.window:
            s = {"count": 0, "first_ts": now, "next_allowed": 0}

        s["count"] += 1
        self.state[key] = s

        if s["count"] >= rule.threshold:
            s["next_allowed"] = now + rule.cooldown
            # reset contador para próxima ventana
            s["count"] = 0
            s["first_ts"] = now
            self.state[key] = s
            return {
                "emit": True,
                "grouped": True,
                "count": rule.threshold,
                "next_allowed": s["next_allowed"],
            }
        return {"emit": False}

    def send_alert_with_retry(
        self, url: str, data: dict, max_retries: int = 3, timeout: int = 10
    ):
        """
        Envía alerta con retry y exponential backoff

        Args:
            url: URL del webhook
            data: Datos de la alerta
            max_retries: Número máximo de reintentos
            timeout: Timeout en segundos para cada request
        """
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=data,
                    timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return True, response.status_code

            except requests.exceptions.Timeout:
                print(f"⚠️  Timeout en intento {attempt + 1}/{max_retries}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error en intento {attempt + 1}/{max_retries}: {e}")
            except Exception as e:
                print(
                    f"❌ Error inesperado en intento {attempt + 1}/{max_retries}: {e}"
                )

            # Exponential backoff: esperar 1s, 2s, 4s...
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                print(f"⏳ Esperando {wait_time}s antes del siguiente intento...")
                time.sleep(wait_time)

        print(f"❌ Falló después de {max_retries} intentos")
        return False, None
