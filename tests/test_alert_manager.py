def test_alert_grouping_and_cooldown():
    from p1.alert_manager import AlertManager

    am = AlertManager()
    file = "binance_api.py"
    emitted = []
    # 5 errores rápidos: al 5º debería emitir agrupada
    for _ in range(5):
        res = am.add("error", file, now=1000.0)
        emitted.append(res.get("emit", False))
    assert any(emitted), "Debe emitir alerta agrupada al alcanzar el umbral"
    # Inmediatamente después, en cooldown: no debe emitir
    res = am.add("error", file, now=1001.0)
    assert not res.get("emit", False)
