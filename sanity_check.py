import base64
import json
import os
import sys

import yaml
from dotenv import load_dotenv


def must_env(name):
    val = os.getenv(name)
    if not val:
        print(f"❌ Falta variable de entorno: {name}", file=sys.stderr)
        sys.exit(2)
    return val


def check_base64_service_account():
    b64 = must_env("GOOGLE_SHEETS_CREDENTIALS_B64")
    try:
        js = base64.b64decode(b64).decode("utf-8")
        info = json.loads(js)
        assert info.get("type") == "service_account", "JSON no es de Service Account"
        assert (
            "client_email" in info and "private_key" in info
        ), "Campos clave faltan en JSON"
        print("✅ Service Account base64 válido y completo.")
    except Exception as e:
        print(f"❌ Error en GOOGLE_SHEETS_CREDENTIALS_B64: {e}", file=sys.stderr)
        sys.exit(2)


def main():
    load_dotenv()
    print(f"ℹ️ Python: {sys.version.split()[0]}")

    must_env("EVENT_SHEET_ID")
    check_base64_service_account()

    try:
        from eventarb.core.logging_setup import setup_logging
        from eventarb.core.planner import plan_actions_for_event
        from eventarb.ingest.sheets_reader import read_events_from_sheet

        logger = setup_logging()
        with open("config/settings.yaml", "r") as f:
            cfg = yaml.safe_load(f)
        default_notional = float(cfg.get("default_notional_usd", 50.0))

        evs = read_events_from_sheet()
        if not evs:
            print("⚠️ Lector OK, pero no hay eventos habilitados válidos.")
            sys.exit(0)

        print(f"✅ {len(evs)} evento(s) leídos.")
        acts = plan_actions_for_event(evs[0], default_notional)
        print(f"✅ Planner generó {len(acts)} acción(es) para {evs[0].id}.")
        if acts:
            a = acts[0]
            print(
                f"   → {a.symbol} {a.side} notional=${a.notional_usd} TP={a.tp_pct}% SL={a.sl_pct}% timing={a.timing}"
            )
        print("🎉 Sanity check completado.")
    except Exception as e:
        print(f"❌ Falla en flujo mínimo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
