# P1 Sprint – Reporting & Monitoring Bootstrap

## Qué incluye
- **Sheets (stub)**: `p1/sheets_handler.py` con NO-OP seguro cuando `GOOGLE_SHEETS_DISABLED=1`.
- **Alertas agrupadas + cooldown**: `p1/alert_manager.py`.
- **Contador & PnL día**: `p1/daily_counter.py` (SQLite).
- **Dashboard FastAPI**: `p1.dashboard:/metrics` con métricas base.
- **Tests**: `tests/` para los 4 módulos (sin red), CI en Python 3.12.x.

## Cómo probar
- `pytest -q` → todo verde sin credenciales.
- `uvicorn p1.dashboard:app --port 8000` y visitar `/metrics`.
- (Sheets real) exportar `GOOGLE_SHEETS_CREDENTIALS_B64` y `GOOGLE_SHEET_ID`, y desactivar `GOOGLE_SHEETS_DISABLED`.

## Definition of Done (P1)
- [ ] TRADE_CLOSED real registrado en **Sheets** (TradesClosed + DailySummary).
- [ ] Alerta **ALERT_GROUPED** con cooldown 5 min demostrada.
- [ ] Dashboard operativo y mostrando métricas en vivo.
- [ ] E2E (con mocks) pasando en CI.

## Notas
- Python **3.12.x** fijado en CI (matrix).
- No se toca la lógica de trading ni límites; solo observabilidad/monitoring.
