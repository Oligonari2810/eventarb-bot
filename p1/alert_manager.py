from __future__ import annotations

import time
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
