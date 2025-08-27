"""
Utilidades para Google Sheets con filtros robustos
Previene mezcla de eventos con órdenes
"""

import os
import re
from typing import Any, Dict, Optional

# Tipos de eventos permitidos
ALLOWED_KINDS = {
    "CPI",
    "FOMC",
    "EARNINGS",
    "NFP",
    "PMI",
    "GDP",
    "RETAIL_SALES",
    "UNEMPLOYMENT",
    "HOUSING",
    "MANUFACTURING",
}


def is_true(x) -> bool:
    """Verifica si un valor es verdadero"""
    if x is None:
        return False
    return str(x).strip().upper() in {"1", "TRUE", "YES", "ON"}


def is_valid_event_kind(kind: str) -> bool:
    """Verifica si el tipo de evento es válido"""
    if not kind:
        return False
    return str(kind).strip().upper() in ALLOWED_KINDS


def contains_trade_keywords(text: str) -> bool:
    """Detecta si un texto contiene palabras clave de trading"""
    if not text:
        return False

    text_upper = f" {str(text).upper()} "
    trade_keywords = [
        " BUY ",
        " SELL ",
        " LONG ",
        " SHORT ",
        " ENTRY ",
        " EXIT ",
        " TP ",
        " SL ",
        " STOP LOSS ",
        " TAKE PROFIT ",
        " POSITION ",
        " ORDER ",
        " FILL ",
        " EXECUTE ",
        " MARKET ",
        " LIMIT ",
    ]

    return any(keyword in text_upper for keyword in trade_keywords)


def parse_event_row(row: list) -> Optional[Dict[str, Any]]:
    """
    Parsea una fila de evento con validaciones robustas

    Espera: id, kind, t0_iso, symbols_csv, consensus, note, enabled
    """
    if not row or len(row) < 7:
        return None

    # Extraer campos
    id_, kind, t0_iso, syms, cons, note, en = row[:7]

    # Validaciones críticas
    if not id_ or not kind or not t0_iso:
        return None

    if not is_valid_event_kind(kind):
        return None

    if not is_true(en):
        return None

    # ANTI-MEZCLA: si la fila tiene palabras clave de trading, NO es un evento
    joined = " ".join(str(x) for x in row if x)
    if contains_trade_keywords(joined):
        return None

    # Validar formato de fecha ISO
    if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?$", str(t0_iso)):
        return None

    # Validar símbolos
    if not syms or not str(syms).strip():
        return None

    return {
        "id": str(id_).strip(),
        "kind": str(kind).strip().upper(),
        "t0_iso": str(t0_iso).strip(),
        "symbols_csv": str(syms).strip(),
        "consensus": str(cons).strip() if cons else "",
        "note": str(note).strip() if note else "",
        "enabled": True,
    }


def assert_distinct_event_trade_targets():
    """
    Verifica que EVENT y TRADES apuntan a objetivos distintos
    Previene mezcla de datos
    """
    ev_id = os.getenv("EVENT_SHEET_ID", "")
    tr_id = os.getenv("TRADES_SHEET_ID", "")

    if not ev_id or not tr_id:
        raise RuntimeError("EVENT_SHEET_ID o TRADES_SHEET_ID no configurados")

    ev_range = os.getenv("EVENT_SHEET_RANGE", "")
    tr_range = os.getenv("TRADES_SHEET_RANGE", "")

    if not ev_range or not tr_range:
        raise RuntimeError("EVENT_SHEET_RANGE o TRADES_SHEET_RANGE no configurados")

    # Extraer nombres de pestañas
    ev_tab = ev_range.split("!", 1)[0] if "!" in ev_range else ""
    tr_tab = tr_range.split("!", 1)[0] if "!" in tr_range else ""

    # No permitir mismo documento y misma pestaña
    if ev_id == tr_id and ev_tab == tr_tab:
        raise RuntimeError(
            f"Configuración inválida: EVENT y TRADES apuntan a la misma pestaña '{ev_tab}'. "
            "Deben ser pestañas distintas o documentos distintos antes de escribir."
        )

    return True


def clean_decimal_value(value: str) -> float:
    """
    Convierte valores con coma decimal a punto decimal
    Útil para datos de Google Sheets con formato europeo
    """
    if value is None:
        return 0.0

    # Convertir a string y limpiar
    str_value = str(value).strip()

    # Reemplazar coma por punto
    str_value = str_value.replace(",", ".")

    try:
        return float(str_value)
    except ValueError:
        return 0.0
