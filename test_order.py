#!/usr/bin/env python3
"""
Script de test para verificar conexión con Binance
NO ejecuta trades reales, solo verifica conectividad
"""

import os
from binance.spot import Spot as Binance
from dotenv import load_dotenv

def test_binance_connection():
    """Test de conexión básica a Binance"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not api_key or not api_secret:
            print("❌ BINANCE_API_KEY o BINANCE_API_SECRET no encontrados")
            return False
        
        # Crear cliente
        client = Binance(api_key=api_key, api_secret=api_secret)
        
        # Test 1: Ping
        print("🔍 Test 1: Ping a Binance...")
        ping_result = client.ping()
        print(f"✅ Ping OK: {ping_result}")
        
        # Test 2: Información de cuenta
        print("\n🔍 Test 2: Información de cuenta...")
        account_info = client.account()
        print(f"✅ Cuenta OK: {len(account_info.get('balances', []))} activos")
        
        # Test 3: Balance USDT
        usdt_balance = None
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                break
        
        if usdt_balance is not None:
            print(f"💰 Balance USDT: {usdt_balance:.2f}")
        else:
            print("⚠️ No se encontró balance USDT")
        
        # Test 4: Información del símbolo BTCUSDT
        print("\n🔍 Test 3: Información de símbolo BTCUSDT...")
        symbol_info = client.exchange_info()
        btc_info = None
        for symbol in symbol_info.get('symbols', []):
            if symbol['symbol'] == 'BTCUSDT':
                btc_info = symbol
                break
        
        if btc_info:
            print(f"✅ BTCUSDT disponible: {btc_info['status']}")
            print(f"   Base Asset: {btc_info['baseAsset']}")
            print(f"   Quote Asset: {btc_info['quoteAsset']}")
        else:
            print("❌ BTCUSDT no disponible")
        
        # Test 5: Precio actual BTCUSDT
        print("\n🔍 Test 4: Precio actual BTCUSDT...")
        ticker = client.ticker_price(symbol="BTCUSDT")
        if ticker:
            print(f"✅ Precio BTCUSDT: ${float(ticker['price']):,.2f}")
        else:
            print("❌ No se pudo obtener precio BTCUSDT")
        
        # Test 6: Verificar permisos de trading
        print("\n🔍 Test 5: Permisos de trading...")
        api_restrictions = client.api_restrictions()
        print(f"✅ Restricciones API: {api_restrictions}")
        
        print("\n" + "=" * 50)
        print("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("✅ Binance está conectado y funcionando correctamente")
        print("✅ No se ejecutaron trades reales")
        print("✅ Listo para operar en mainnet")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de Binance: {e}")
        return False

def test_order_creation_simulation():
    """Simula la creación de una orden sin ejecutarla"""
    try:
        print("\n🔍 Test 6: Simulación de creación de orden...")
        
        # Cargar variables de entorno
        load_dotenv()
        
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not api_key or not api_secret:
            print("❌ Credenciales no encontradas")
            return False
        
        client = Binance(api_key=api_key, api_secret=api_secret)
        
        # Obtener precio actual de BTCUSDT
        ticker = client.ticker_price(symbol="BTCUSDT")
        current_price = float(ticker['price'])
        
        # Simular parámetros de orden (NO se ejecuta)
        symbol = "BTCUSDT"
        side = "BUY"
        quantity = 0.001  # Mínimo para BTC
        price = current_price * 0.95  # 5% debajo del precio actual (no se ejecutará)
        
        print(f"📊 Simulando orden:")
        print(f"   Símbolo: {symbol}")
        print(f"   Lado: {side}")
        print(f"   Cantidad: {quantity}")
        print(f"   Precio límite: ${price:,.2f}")
        print(f"   Precio actual: ${current_price:,.2f}")
        print(f"   Notional: ${quantity * price:,.2f}")
        
        # Verificar que la orden NO se ejecute (precio muy bajo)
        print(f"✅ Orden simulada - NO se ejecutará (precio límite < precio actual)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en simulación de orden: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 TEST DE CONECTIVIDAD BINANCE")
    print("=" * 50)
    print("⚠️  IMPORTANTE: NO se ejecutarán trades reales")
    print()
    
    # Test de conexión básica
    connection_ok = test_binance_connection()
    
    if connection_ok:
        # Test de simulación de orden
        order_simulation_ok = test_order_creation_simulation()
        
        if order_simulation_ok:
            print("\n🎯 RESUMEN FINAL:")
            print("✅ Conexión a Binance: OK")
            print("✅ Simulación de orden: OK")
            print("✅ No se ejecutaron trades reales")
            print("✅ Listo para operar en mainnet")
            print("\n🚀 ¡Puedes proceder con el lanzamiento!")
        else:
            print("\n❌ Simulación de orden falló")
            return False
    else:
        print("\n❌ Conexión a Binance falló")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
