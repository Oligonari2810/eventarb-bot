"""
Modelos de datos para EventArb Bot
Definición de las estructuras de datos principales
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Literal

Side = Literal["BUY", "SELL", "FLAT"]

@dataclass
class Event:
    id: str
    kind: str                 # "CPI", "FOMC", ...
    t0_iso: str               # ISO-UTC con 'Z'
    symbols: List[str]        # ["BTCUSDT", "ETHUSDT"]
    consensus: Optional[float] = None
    note: str = ""

@dataclass
class PlannedAction:
    event_id: str
    symbol: str               # "BTCUSDT"
    side: Side                # BUY/SELL/FLAT
    notional_usd: Decimal
    tp_pct: float
    sl_pct: float
    timing: str               # "AT_T0" | "T_MINUS_30M" | ...
