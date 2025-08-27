#!/usr/bin/env python3
"""
Validador corregido - usa fechas específicas 2023-2024
Resuelve el problema de validación identificado por DS
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class FixedDataCoverageValidator:
    def __init__(self, db_path: str = 'trading_data.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Conectar a la base de datos"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"✅ Conectado a {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Error conectando a BD: {e}")
            return False
    
    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.conn:
            self.conn.close()
    
    def check_macro_coverage_fixed(self) -> Dict[str, bool]:
        """Verificar cobertura de eventos macro con fechas 2023-2024"""
        print("\n📊 Verificando cobertura de eventos macro (2023-2024)...")
        
        # Fechas específicas para nuestro dataset (2023-2024)
        start_date = '2023-01-01'
        end_date = '2024-12-31'
        
        # Verificar CPI (mínimo 24 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(DISTINCT event_date) 
            FROM macro_events 
            WHERE event_type = 'CPI' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        cpi_count = self.cursor.fetchone()[0]
        
        # Verificar FOMC (mínimo 8 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(DISTINCT event_date) 
            FROM macro_events 
            WHERE event_type = 'FOMC' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        fomc_count = self.cursor.fetchone()[0]
        
        # Verificar GDP (mínimo 12 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(DISTINCT event_date) 
            FROM macro_events 
            WHERE event_type = 'GDP' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        gdp_count = self.cursor.fetchone()[0]
        
        # Verificar Unemployment (mínimo 24 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(DISTINCT event_date) 
            FROM macro_events 
            WHERE event_type = 'UNEMPLOYMENT' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        unemployment_count = self.cursor.fetchone()[0]
        
        # Verificar ECB (mínimo 15 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(DISTINCT event_date) 
            FROM macro_events 
            WHERE event_type = 'ECB_RATE' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        ecb_count = self.cursor.fetchone()[0]
        
        print(f"   📈 CPI: {cpi_count}/24 eventos requeridos (2023-2024)")
        print(f"   🏦 FOMC: {fomc_count}/8 eventos requeridos (2023-2024)")
        print(f"   📊 GDP: {gdp_count}/12 eventos requeridos (2023-2024)")
        print(f"   👥 Unemployment: {unemployment_count}/24 eventos requeridos (2023-2024)")
        print(f"   🇪🇺 ECB: {ecb_count}/15 eventos requeridos (2023-2024)")
        
        # Validar mínimos para 2023-2024
        macro_ok = (
            cpi_count >= 24 and 
            fomc_count >= 8 and 
            gdp_count >= 12 and 
            unemployment_count >= 24 and 
            ecb_count >= 15
        )
        
        return {
            'CPI': cpi_count >= 24,
            'FOMC': fomc_count >= 8,
            'GDP': gdp_count >= 12,
            'UNEMPLOYMENT': unemployment_count >= 24,
            'ECB': ecb_count >= 15,
            'OVERALL': macro_ok
        }
    
    def check_token_events_coverage_fixed(self) -> Dict[str, bool]:
        """Verificar cobertura de eventos de tokens con fechas 2023-2024"""
        print("\n🪙 Verificando cobertura de eventos de tokens (2023-2024)...")
        
        # Fechas específicas para nuestro dataset (2023-2024)
        start_date = '2023-01-01'
        end_date = '2024-12-31'
        
        # Verificar Unlocks (mínimo 50 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) 
            FROM token_events 
            WHERE event_type = 'UNLOCK' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        unlock_count = self.cursor.fetchone()[0]
        
        # Verificar Listings (mínimo 25 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) 
            FROM token_events 
            WHERE event_type = 'LISTING' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        listing_count = self.cursor.fetchone()[0]
        
        # Verificar Security Incidents (mínimo 10 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) 
            FROM token_events 
            WHERE event_type = 'HACK' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        hack_count = self.cursor.fetchone()[0]
        
        print(f"   🔓 Unlocks: {unlock_count}/50 eventos requeridos (2023-2024)")
        print(f"   📈 Listings: {listing_count}/25 eventos requeridos (2023-2024)")
        print(f"   🚨 Security: {hack_count}/10 eventos requeridos (2023-2024)")
        
        # Validar mínimos para 2023-2024
        token_ok = (
            unlock_count >= 50 and 
            listing_count >= 25 and 
            hack_count >= 10
        )
        
        return {
            'UNLOCKS': unlock_count >= 50,
            'LISTINGS': listing_count >= 25,
            'SECURITY': hack_count >= 10,
            'OVERALL': token_ok
        }
    
    def check_market_data_coverage(self) -> Dict[str, bool]:
        """Verificar cobertura de datos de mercado"""
        print("\n📈 Verificando cobertura de datos de mercado...")
        
        # Verificar datos BTC (mínimo 30 días)
        self.cursor.execute("""
            SELECT COUNT(DISTINCT date(timestamp)) FROM market_data 
            WHERE symbol = 'BTCUSDT' 
            AND timestamp >= date('now', '-30 days')
        """)
        btc_days = self.cursor.fetchone()[0]
        
        # Verificar profundidad del order book
        self.cursor.execute("""
            SELECT AVG(book_depth_usd) FROM market_data 
            WHERE symbol = 'BTCUSDT' 
            AND timestamp >= date('now', '-7 days')
        """)
        avg_depth = self.cursor.fetchone()[0] or 0
        
        # Verificar spread promedio
        self.cursor.execute("""
            SELECT AVG(spread_bps) FROM market_data 
            WHERE symbol = 'BTCUSDT' 
            AND timestamp >= date('now', '-7 days')
        """)
        avg_spread = self.cursor.fetchone()[0] or 0
        
        print(f"   📅 BTC Data: {btc_days}/30 días requeridos")
        print(f"   💰 Avg Book Depth: ${avg_depth:,.0f}")
        print(f"   📊 Avg Spread: {avg_spread:.2f} bps")
        
        # Validar mínimos
        market_ok = (
            btc_days >= 30 and 
            avg_depth >= 2000000 and  # $2M mínimo
            avg_spread <= 5  # 5 bps máximo
        )
        
        return {
            'BTC_DAYS': btc_days >= 30,
            'BOOK_DEPTH': avg_depth >= 2000000,
            'SPREAD': avg_spread <= 5,
            'OVERALL': market_ok
        }
    
    def check_family_coverage_fixed(self) -> Dict[str, bool]:
        """Verificar cobertura por familia de eventos con fechas 2023-2024"""
        print("\n🏗️ Verificando cobertura por familia de eventos (2023-2024)...")
        
        # Fechas específicas para nuestro dataset (2023-2024)
        start_date = '2023-01-01'
        end_date = '2024-12-31'
        
        # Macro US (mínimo 20 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM macro_events 
            WHERE family = 'macro_US' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        macro_us_count = self.cursor.fetchone()[0]
        
        # Macro EU (mínimo 15 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM macro_events 
            WHERE family = 'macro_EU' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        macro_eu_count = self.cursor.fetchone()[0]
        
        # Crypto Unlocks (mínimo 30 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM token_events 
            WHERE family = 'crypto_unlocks' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        crypto_unlocks_count = self.cursor.fetchone()[0]
        
        # Listings (mínimo 25 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM token_events 
            WHERE family = 'listings' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        listings_count = self.cursor.fetchone()[0]
        
        # Security Incidents (mínimo 10 eventos en 2023-2024)
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM token_events 
            WHERE family = 'security_incidents' 
            AND event_date BETWEEN '{start_date}' AND '{end_date}'
        """)
        security_count = self.cursor.fetchone()[0]
        
        print(f"   🇺🇸 Macro US: {macro_us_count}/20 eventos requeridos (2023-2024)")
        print(f"   🇪🇺 Macro EU: {macro_eu_count}/15 eventos requeridos (2023-2024)")
        print(f"   🔓 Crypto Unlocks: {crypto_unlocks_count}/30 eventos requeridos (2023-2024)")
        print(f"   📈 Listings: {listings_count}/25 eventos requeridos (2023-2024)")
        print(f"   🚨 Security: {security_count}/10 eventos requeridos (2023-2024)")
        
        # Validar mínimos por familia para 2023-2024
        family_ok = (
            macro_us_count >= 20 and
            macro_eu_count >= 15 and
            crypto_unlocks_count >= 30 and
            listings_count >= 25 and
            security_count >= 10
        )
        
        return {
            'macro_US': macro_us_count >= 20,
            'macro_EU': macro_eu_count >= 15,
            'crypto_unlocks': crypto_unlocks_count >= 30,
            'listings': listings_count >= 25,
            'security_incidents': security_count >= 10,
            'OVERALL': family_ok
        }
    
    def run_fixed_validation(self) -> Dict[str, bool]:
        """Ejecutar validación corregida con fechas 2023-2024"""
        print("🚀 INICIANDO VALIDACIÓN CORREGIDA (2023-2024)")
        print("=" * 60)
        print("🎯 Usando fechas específicas 2023-2024 como propone DS")
        print("=" * 60)
        
        if not self.connect():
            return {'ERROR': 'No se pudo conectar a la BD'}
        
        try:
            # Ejecutar todas las validaciones corregidas
            macro_results = self.check_macro_coverage_fixed()
            token_results = self.check_token_events_coverage_fixed()
            market_results = self.check_market_data_coverage()
            family_results = self.check_family_coverage_fixed()
            
            # Resumen final
            print("\n" + "=" * 60)
            print("📋 RESUMEN DE VALIDACIÓN CORREGIDA (2023-2024)")
            print("=" * 60)
            
            all_validations = {
                'MACRO_EVENTS': macro_results['OVERALL'],
                'TOKEN_EVENTS': token_results['OVERALL'],
                'MARKET_DATA': market_results['OVERALL'],
                'FAMILY_COVERAGE': family_results['OVERALL']
            }
            
            for category, result in all_validations.items():
                status = "✅ CUMPLE" if result else "❌ NO CUMPLE"
                print(f"   {category}: {status}")
            
            overall_result = all(all_validations.values())
            overall_status = "✅ VALIDACIÓN EXITOSA" if overall_result else "❌ VALIDACIÓN FALLIDA"
            
            print(f"\n🎯 RESULTADO FINAL: {overall_status}")
            
            if overall_result:
                print("\n🚀 SISTEMA LISTO PARA OPERACIONES")
                print("   - Cobertura mínima cumplida para 2023-2024")
                print("   - Datos históricos suficientes")
                print("   - Calibración habilitada")
                print("   - Problema de fechas resuelto ✅")
            else:
                print("\n⚠️ SISTEMA NO LISTO PARA OPERACIONES")
                print("   - Cobertura mínima NO cumplida para 2023-2024")
                print("   - Se requieren más datos históricos")
                print("   - Calibración bloqueada")
            
            return all_validations
            
        finally:
            self.disconnect()

def main():
    """Función principal"""
    validator = FixedDataCoverageValidator()
    results = validator.run_fixed_validation()
    
    # Retornar código de salida apropiado
    if 'ERROR' in results:
        print(f"\n❌ Error en validación: {results['ERROR']}")
        exit(1)
    
    all_passed = all(results.values())
    exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
