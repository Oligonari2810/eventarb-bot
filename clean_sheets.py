#!/usr/bin/env python3
"""
Script de limpieza para Google Sheets
Reorganiza datos y crea pestañas separadas para Events y Trades
"""

import base64
import json
import os
import sys

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def load_sheets_service():
    """Cargar servicio de Google Sheets"""
    try:
        b64 = os.environ["GOOGLE_SHEETS_CREDENTIALS_B64"].strip()
        b64_clean = "".join(b64.split())

        # Corregir padding si falta
        missing = len(b64_clean) % 4
        if missing:
            b64_clean += "=" * (4 - missing)

        creds_dict = json.loads(base64.b64decode(b64_clean).decode())
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        print(f"❌ Error cargando credenciales: {e}")
        return None


def clean_and_organize_sheets():
    """Limpiar y reorganizar el Google Sheets"""
    print("🧹 LIMPIEZA Y REORGANIZACIÓN DE GOOGLE SHEETS")
    print("=" * 50)

    # Cargar servicio
    service = load_sheets_service()
    if not service:
        return False

    sheet_id = os.getenv("EVENT_SHEET_ID")
    if not sheet_id:
        print("❌ EVENT_SHEET_ID no configurado")
        return False

    try:
        # Leer datos actuales de la pestaña principal
        print("📖 Leyendo datos actuales...")
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range="A2:G200")
            .execute()
        )

        rows = result.get("values", [])
        if not rows:
            print("❌ No se encontraron datos")
            return False

        print(f"📊 {len(rows)} filas encontradas")

        # Separar eventos válidos de órdenes
        valid_events = []
        trade_orders = []

        for i, row in enumerate(rows, start=2):
            if len(row) >= 7:
                # Verificar si es un evento válido
                id_, kind, t0_iso, syms, cons, note, en = row[:7]

                # Detectar si es evento o orden
                row_text = " ".join(str(x) for x in row if x).upper()
                is_trade = any(
                    keyword in row_text
                    for keyword in ["BUY", "SELL", "LONG", "SHORT", "ENTRY", "EXIT"]
                )

                if is_trade:
                    trade_orders.append(row)
                elif kind and kind.strip() and t0_iso and syms:
                    # Es un evento válido
                    valid_events.append(row)

        print(f"✅ {len(valid_events)} eventos válidos encontrados")
        print(f"📈 {len(trade_orders)} órdenes de trading encontradas")

        # Crear pestaña Events si no existe
        print("\n📋 Creando pestaña 'Events'...")
        try:
            # Intentar crear pestaña
            request = {
                "addSheet": {
                    "properties": {
                        "title": "Events",
                        "gridProperties": {"rowCount": 1000, "columnCount": 10},
                    }
                }
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body={"requests": [request]}
            ).execute()
            print("✅ Pestaña 'Events' creada")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Pestaña 'Events' ya existe")
            else:
                print(f"⚠️  Error creando pestaña: {e}")

        # Crear pestaña Trades si no existe
        print("📋 Creando pestaña 'Trades'...")
        try:
            request = {
                "addSheet": {
                    "properties": {
                        "title": "Trades",
                        "gridProperties": {"rowCount": 2000, "columnCount": 15},
                    }
                }
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body={"requests": [request]}
            ).execute()
            print("✅ Pestaña 'Trades' creada")
        except Exception as e:
            if "already exists" in str(e):
                print("ℹ️  Pestaña 'Trades' ya existe")
            else:
                print(f"⚠️  Error creando pestaña: {e}")

        # Escribir eventos válidos en pestaña Events
        if valid_events:
            print(
                f"\n📝 Escribiendo {len(valid_events)} eventos en pestaña 'Events'..."
            )

            # Agregar headers
            headers = [
                "id",
                "kind",
                "t0_iso",
                "symbols_csv",
                "consensus",
                "note",
                "enabled",
            ]
            all_events = [headers] + valid_events

            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range="Events!A1",
                valueInputOption="RAW",
                body={"values": all_events},
            ).execute()

            print("✅ Eventos escritos en pestaña 'Events'")

        # Escribir órdenes en pestaña Trades (si quieres conservarlas)
        if trade_orders:
            print(
                f"\n📝 Escribiendo {len(trade_orders)} órdenes en pestaña 'Trades'..."
            )

            # Headers para trades
            trade_headers = [
                "id",
                "symbol",
                "side",
                "quantity",
                "entry_price",
                "tp_price",
                "sl_price",
                "risk_pct",
                "enabled",
                "created_at",
                "closed_at",
                "pnl_usd",
            ]
            all_trades = [trade_headers] + trade_orders

            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range="Trades!A1",
                valueInputOption="RAW",
                body={"values": all_trades},
            ).execute()

            print("✅ Órdenes escritas en pestaña 'Trades'")

        print("\n🎯 LIMPIEZA COMPLETADA")
        print("✅ Pestaña 'Events' creada con eventos válidos")
        print("✅ Pestaña 'Trades' creada con órdenes")
        print("✅ Configuración separada implementada")

        return True

    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 INICIANDO LIMPIEZA DE GOOGLE SHEETS")
    print("=" * 50)

    # Cargar variables de entorno
    export_cmd = "export $(grep -v '^#' .env.production | xargs)"
    os.system(export_cmd)

    success = clean_and_organize_sheets()

    if success:
        print("\n🎉 ¡LIMPIEZA EXITOSA!")
        print("📝 PRÓXIMOS PASOS:")
        print("1. Verificar pestañas creadas en Google Sheets")
        print("2. Proteger pestaña 'Events' (solo lectura para el bot)")
        print("3. Ejecutar: python check_live_readiness.py")
        print("4. Arrancar el bot: ./run_forever.sh")
    else:
        print("\n❌ LIMPIEZA FALLIDA")
        print("Revisar errores y ejecutar manualmente")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
