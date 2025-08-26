from fastapi.testclient import TestClient

from p1.dashboard import app


def test_metrics_endpoint_ok():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    for k in (
        "trades_today",
        "win_rate",
        "pnl_day",
        "state",
        "last_trade_ts",
        "uptime",
    ):
        assert k in data
