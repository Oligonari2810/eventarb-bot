"""
Lector de Google Sheets para EventArb Bot
Maneja la lectura y procesamiento de datos desde Google Sheets
"""

import base64
import json
import os
from typing import List, Tuple

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from eventarb.core.models import Event

VALID_ENABLED = {"1", "true", "yes", "y"}


def _decode_service_account():
    b64 = os.getenv("GOOGLE_SHEETS_CREDENTIALS_B64")
    if not b64:
        raise RuntimeError("GOOGLE_SHEETS_CREDENTIALS_B64 vacío")

    # LIMPIAR el base64 - eliminar saltos de línea y espacios
    b64_clean = b64.replace("\n", "").replace(" ", "")

    try:
        creds_json = base64.b64decode(b64_clean).decode("utf-8")
        info = json.loads(creds_json)
        if info.get("type") != "service_account":
            raise RuntimeError("El JSON no es de Service Account")
        return info
    except Exception as e:
        raise RuntimeError(f"Error decodificando/parseando credenciales: {e}")


def _sheets_service():
    info = _decode_service_account()
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def _normalize_symbols(symbols_csv: str) -> List[str]:
    seen = set()
    out: List[str] = []
    for raw in (symbols_csv or "").split(","):
        s = raw.strip().upper()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _is_enabled(val: str) -> bool:
    return (val or "").strip().lower() in VALID_ENABLED


def _validate_row_fields(row: List[str], idx: int) -> Tuple[bool, str]:
    """Valida formato mínimo:
    - 7 columnas
    - t0_iso termina en 'Z'
    - symbols no vacío si enabled
    """
    if len(row) < 7:
        return False, f"Fila {idx}: incompleta (<7 columnas)"
    id_, kind, t0_iso, symbols_csv, consensus, note, enabled = (row + [""] * 7)[:7]
    if not t0_iso.strip().endswith("Z"):
        return False, f"Fila {idx}: t0_iso no está en formato UTC (falta 'Z')"
    if _is_enabled(enabled) and not _normalize_symbols(symbols_csv):
        return False, f"Fila {idx}: symbols_csv vacío con enabled activo"
    return True, ""


def read_events_from_sheet() -> List[Event]:
    """Lee la Sheet y devuelve eventos válidos (habilitados y con formato correcto).
    Si Sheets falla, lanza RuntimeError (que el caller puede atrapar para modo demo).
    """
    sheet_id = os.getenv("EVENT_SHEET_ID")
    rng = os.getenv("EVENT_SHEET_RANGE", "A2:G200")
    if not sheet_id:
        raise RuntimeError("EVENT_SHEET_ID vacío")

    svc = _sheets_service()
    # Encabezados A1:G1 (opcional)
    try:
        hdr = (
            svc.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range="A1:G1")
            .execute()
            .get("values", [[]])[0]
        )
    except Exception:
        hdr = []

    # Lectura principal
    try:
        resp = (
            svc.spreadsheets().values().get(spreadsheetId=sheet_id, range=rng).execute()
        )
    except Exception as e:
        raise RuntimeError(f"No se pudo leer la Sheet: {e}")

    rows = resp.get("values", [])
    events: List[Event] = []

    # A:id B:kind C:t0_iso D:symbols_csv E:consensus F:note G:enabled
    for i, r in enumerate(rows, start=2):  # fila 2 corresponde a A2
        ok, msg = _validate_row_fields(r, i)
        if not ok:
            # se omite la fila inválida, el caller la logueará como WARNING si quiere
            # aquí no levantamos excepción para permitir que otras filas pasen
            print(f"WARNING - {msg}")
            continue

        id_, kind, t0_iso, symbols_csv, consensus, note, enabled = (r + [""] * 7)[:7]
        if not _is_enabled(enabled):
            # deshabilitado silenciosamente
            continue

        syms = _normalize_symbols(symbols_csv)
        cons_val = None
        if consensus and consensus.strip():
            try:
                cons_val = float(consensus)
            except Exception:
                print(f"WARNING - Fila {i}: consensus no numérico, se usará None")

        events.append(
            Event(
                id=id_.strip(),
                kind=(kind or "").strip().upper(),
                t0_iso=t0_iso.strip(),
                symbols=syms,
                consensus=cons_val,
                note=(note or "").strip(),
            )
        )

    return events
