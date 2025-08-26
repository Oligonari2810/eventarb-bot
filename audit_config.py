#!/usr/bin/env python3
"""
Auditor de configuración para EventArb Bot
Verifica que EVENT y TRADES estén en documentos/pestañas separadas
"""

import os
import re
import sys


def tab_from_range(r):
    """Extrae el nombre de la pestaña del rango"""
    if not r:
        return None
    m = re.match(r"^([^!]+)![A-Z]+\d+:[A-Z]+\d+$", r)
    return m.group(1) if m else None


def main():
    print("🔍 AUDITOR DE CONFIGURACIÓN EVENTARB BOT")
    print("=" * 50)

    # Leer variables de entorno
    ev_id = os.getenv("EVENT_SHEET_ID")
    tr_id = os.getenv("TRADES_SHEET_ID")
    ev_rg = os.getenv("EVENT_SHEET_RANGE")
    tr_rg = os.getenv("TRADES_SHEET_RANGE")

    print(f"📊 EVENT_SHEET_ID: {ev_id}")
    print(f"📊 TRADES_SHEET_ID: {tr_id}")
    print(f"📊 EVENT_SHEET_RANGE: {ev_rg}")
    print(f"📊 TRADES_SHEET_RANGE: {tr_rg}")
    print()

    errors = []

    # Verificar que existan todas las variables
    if not ev_id or not tr_id or not ev_rg or not tr_rg:
        errors.append("❌ Faltan variables EVENT_/TRADES_ en .env.production")

    # Extraer nombres de pestañas
    ev_tab = tab_from_range(ev_rg)
    tr_tab = tab_from_range(tr_rg)

    print(f"📋 Pestaña Events: {ev_tab}")
    print(f"📋 Pestaña Trades: {tr_tab}")
    print()

    # Verificar separación
    if ev_id == tr_id and ev_tab and tr_tab and ev_tab == tr_tab:
        errors.append(
            "❌ EVENT y TRADES apuntan a **LA MISMA PESTAÑA**. Deben ser pestañas distintas o documentos distintos."
        )

    if ev_tab is None or tr_tab is None:
        errors.append("❌ Rangos mal formados. Usa formato: Tab!A2:G200")

    # Verificar formato de rangos
    if ev_rg and not re.match(r"^[^!]+![A-Z]+\d+:[A-Z]+\d+$", ev_rg):
        errors.append("❌ EVENT_SHEET_RANGE mal formado. Usa: Events!A2:G200")

    if tr_rg and not re.match(r"^[^!]+![A-Z]+\d+:[A-Z]+\d+$", tr_rg):
        errors.append("❌ TRADES_SHEET_RANGE mal formado. Usa: Trades!A2:L2000")

    # Resultado
    if errors:
        print("❌ AUDIT FAILED")
        print("=" * 30)
        for e in errors:
            print(f" - {e}")
        print()
        print("🔧 SOLUCIONES:")
        print("1. Usar documentos separados para Events y Trades")
        print("2. O usar pestañas distintas en el mismo documento")
        print("3. Proteger rango de Events (solo lectura para el bot)")
        sys.exit(1)

    print("✅ AUDIT OK: IDs y pestañas separadas correctamente.")
    print("✅ Configuración de Sheets válida.")
    print()
    print("📝 RECOMENDACIONES:")
    print("- Events: solo lectura para el bot")
    print("- Trades: solo escritura del bot")
    print("- Usar permisos de Google Sheets para reforzar")


if __name__ == "__main__":
    main()
