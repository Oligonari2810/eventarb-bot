#!/usr/bin/env python3
"""
Verificador de preparación para EventArb Bot
Confirma que Sheets esté configurado correctamente antes de arrancar
"""

import os
import sys

from eventarb.ingest.sheets_reader import read_events_from_sheet


def main():
    print("🔍 VERIFICANDO PREPARACIÓN PARA OPERACIÓN EN VIVO")
    print("=" * 55)

    # Verificar configuración
    print("📊 Verificando configuración...")
    export_cmd = "export $(grep -v '^#' .env.production | xargs)"
    os.system(export_cmd)

    # Verificar variables críticas
    required_vars = [
        "EVENT_SHEET_ID",
        "TRADES_SHEET_ID",
        "EVENT_SHEET_RANGE",
        "TRADES_SHEET_RANGE",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Variables faltantes: {', '.join(missing_vars)}")
        return False

    print("✅ Configuración básica OK")

    # Verificar conexión a Sheets
    print("📋 Verificando conexión a Google Sheets...")
    try:
        events = read_events_from_sheet()
        if not events:
            print("❌ No se pudieron leer eventos de Sheets")
            print("   Verificar:")
            print("   1. Pestaña 'Events' existe")
            print("   2. Permisos del service account")
            print("   3. Formato de datos correcto")
            return False

        print(f"✅ Sheets OK: {len(events)} eventos leídos")

        # Verificar estructura de eventos
        print("🔍 Verificando estructura de eventos...")
        valid_events = 0
        for event in events:
            if (
                hasattr(event, "id")
                and hasattr(event, "kind")
                and hasattr(event, "symbols")
            ):
                valid_events += 1

        print(f"✅ {valid_events}/{len(events)} eventos con estructura válida")

        if valid_events == 0:
            print("❌ No hay eventos válidos para operar")
            return False

        # Mostrar eventos válidos
        print("\n📅 EVENTOS VÁLIDOS:")
        for event in events[:5]:  # Mostrar solo los primeros 5
            if hasattr(event, "id") and hasattr(event, "kind"):
                symbols_str = (
                    ", ".join(event.symbols) if hasattr(event, "symbols") else "N/A"
                )
                print(f"  - {event.id}: {event.kind} → {symbols_str}")

        if len(events) > 5:
            print(f"  ... y {len(events) - 5} más")

    except Exception as e:
        print(f"❌ Error leyendo Sheets: {e}")
        return False

    # Verificar configuración de Binance
    print("\n🔐 Verificando configuración de Binance...")
    testnet = os.getenv("BINANCE_TESTNET", "0")
    if testnet == "1":
        print("⚠️  ADVERTENCIA: Bot configurado en TESTNET")
    else:
        print("✅ Bot configurado en MAINNET")

    # Verificar kill switch
    kill_switch = os.getenv("KILL_SWITCH", "0")
    if kill_switch == "1":
        print("⚠️  KILL_SWITCH activado - bot no operará")
        return False

    print("\n🎯 RESUMEN DE VERIFICACIÓN:")
    print("✅ Configuración básica")
    print("✅ Conexión a Google Sheets")
    print(f"✅ {valid_events} eventos válidos")
    print("✅ Kill switch desactivado")

    if testnet == "0":
        print("\n🚀 BOT LISTO PARA OPERAR EN MAINNET")
        print("📝 RECOMENDACIONES:")
        print("1. Verificar IP whitelist en Binance")
        print("2. Revisar permisos de Sheets")
        print("3. Monitorear logs durante las primeras operaciones")
    else:
        print("\n🧪 BOT LISTO PARA OPERAR EN TESTNET")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
