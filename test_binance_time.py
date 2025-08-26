#!/usr/bin/env python3
"""
Test rápido para diagnosticar problemas de Binance API
"""

import os

from binance.client import Client


def test_binance_connection():
    """Test de conexión básica a Binance"""
    try:
        # Obtener credenciales del entorno
        api_key = os.environ.get("BINANCE_API_KEY")
        api_secret = os.environ.get("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            print("❌ BINANCE_API_KEY o BINANCE_API_SECRET no encontrados")
            return False

        print(f"🔑 API Key: {api_key[:10]}...")
        print(f"🔐 API Secret: {api_secret[:10]}...")
        print()

        # Crear cliente
        client = Client(api_key=api_key, api_secret=api_secret)

        # 1) Ping público (no usa key)
        print("🔍 Test 1: Ping público...")
        ping_result = client.ping()
        print(f"✅ Ping: {ping_result}")

        # 2) Hora del servidor (para confirmar conexión)
        print("\n🔍 Test 2: Hora del servidor...")
        server_time = client.get_server_time()
        print(f"✅ Server time: {server_time}")

        # 3) Llamada autenticada con recvWindow extendido
        print("\n🔍 Test 3: Llamada autenticada...")
        account_info = client.get_account(recvWindow=5000)
        balances = [b for b in account_info.get("balances", []) if float(b["free"]) > 0]
        print(f"✅ Account balances: {len(balances)} activos con balance")

        # Mostrar algunos balances
        if balances:
            print("💰 Balances principales:")
            for balance in balances[:5]:  # Solo los primeros 5
                print(f"   {balance['asset']}: {float(balance['free']):.6f}")

        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")

        # Diagnóstico específico
        if "Invalid API-key, IP, or permissions" in str(e):
            print(
                "\n🔍 DIAGNÓSTICO: API key inválida, IP bloqueada o permisos insuficientes"
            )
            print("💡 Soluciones:")
            print("   1. Verificar que la API key sea correcta")
            print("   2. Agregar tu IP actual a la whitelist en Binance")
            print("   3. Verificar que tenga permisos de Spot Trading habilitados")
        elif "timestamp" in str(e).lower():
            print("\n🔍 DIAGNÓSTICO: Problema de timestamp")
            print("💡 Solución: Verificar que el reloj de tu sistema esté sincronizado")
        elif "permission" in str(e).lower():
            print("\n🔍 DIAGNÓSTICO: Permisos insuficientes")
            print("💡 Solución: Verificar que la API tenga Spot Trading habilitado")

        return False


def main():
    """Función principal"""
    print("🧪 TEST RÁPIDO DE BINANCE API")
    print("=" * 40)

    # Verificar variables de entorno
    if not os.environ.get("BINANCE_API_KEY") or not os.environ.get(
        "BINANCE_API_SECRET"
    ):
        print("❌ Variables de entorno no configuradas")
        print("💡 Ejecuta: export $(grep -v '^#' .env.production | xargs)")
        return False

    # Ejecutar test
    success = test_binance_connection()

    if success:
        print("\n🎯 RESUMEN:")
        print("✅ Ping: OK")
        print("✅ Server time: OK")
        print("✅ Account access: OK")
        print("✅ Listo para operar en mainnet")
    else:
        print("\n❌ Hay problemas que deben resolverse antes del lanzamiento")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
