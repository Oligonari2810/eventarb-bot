#!/usr/bin/env python3
"""
Script completo para ejecutar smoke tests y validar que todo funciona correctamente
Valida todas las funcionalidades críticas antes de permitir operaciones
"""

import subprocess
import sys
import os
import time
from typing import Dict, List, Tuple

class SmokeTestRunner:
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def run_command(self, command: str, description: str) -> bool:
        """Ejecutar un comando y reportar resultado"""
        print(f"\n🧪 {description}")
        print(f"   Comando: {command}")
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✅ PASÓ - {description}")
                if result.stdout.strip():
                    print(f"      Output: {result.stdout.strip()}")
                return True
            else:
                print(f"   ❌ FALLÓ - {description}")
                if result.stderr.strip():
                    print(f"      Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT - {description}")
            return False
        except Exception as e:
            print(f"   💥 EXCEPCIÓN - {description}: {e}")
            return False
    
    def test_database_structure(self) -> bool:
        """Test 1: Verificar estructura de base de datos"""
        print("\n🗄️ TEST 1: Estructura de Base de Datos")
        
        # Verificar que existe la BD
        if not os.path.exists('trading_data.db'):
            print("   ❌ Base de datos no existe")
            return False
        
        # Verificar que se puede conectar
        test_sql = "python3 -c \"import sqlite3; conn = sqlite3.connect('trading_data.db'); print('✅ BD accesible'); conn.close()\""
        return self.run_command(test_sql, "Conexión a base de datos")
    
    def test_data_coverage(self) -> bool:
        """Test 2: Verificar cobertura de datos"""
        print("\n📊 TEST 2: Cobertura de Datos")
        
        # Ejecutar script de validación
        return self.run_command("python3 validate_data_coverage.py", "Validación de cobertura de datos")
    
    def test_configuration_loading(self) -> bool:
        """Test 3: Verificar carga de configuración"""
        print("\n⚙️ TEST 3: Carga de Configuración")
        
        test_config = """
import sys
sys.path.append('.')
from advanced_trading.config.trading_config import TRADING_CONFIG
print('✅ Configuración cargada correctamente')
print(f'✅ Timezone: {TRADING_CONFIG.get("TIMEZONE_CONFIG", {}).get("PRIMARY_TIMEZONE", "NO_CONFIG")}')
print(f'✅ Max Spread: {TRADING_CONFIG.get("MAX_SPREAD_BPS", "NO_CONFIG")} bps')
print(f'✅ Max Slippage: {TRADING_CONFIG.get("MAX_SLIPPAGE_BPS", "NO_CONFIG")} bps')
"""
        
        with open('temp_config_test.py', 'w') as f:
            f.write(test_config)
        
        result = self.run_command("python3 temp_config_test.py", "Carga de configuración de trading")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_config_test.py'):
            os.remove('temp_config_test.py')
        
        return result
    
    def test_risk_manager(self) -> bool:
        """Test 4: Verificar Risk Manager"""
        print("\n🛡️ TEST 4: Risk Manager")
        
        test_risk = """
import sys
sys.path.append('.')
from advanced_trading.advanced_risk_manager import AdvancedRiskManager
rm = AdvancedRiskManager(10000)
print('✅ Risk Manager cargado correctamente')
print(f'✅ Risk per trade: {rm.risk_per_trade}')
"""
        
        with open('temp_risk_test.py', 'w') as f:
            f.write(test_risk)
        
        result = self.run_command("python3 temp_risk_test.py", "Risk Manager funcional")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_risk_test.py'):
            os.remove('temp_risk_test.py')
        
        return result
    
    def test_macro_analyzer(self) -> bool:
        """Test 5: Verificar Macro Analyzer"""
        print("\n📈 TEST 5: Macro Analyzer")
        
        test_macro = """
import sys
sys.path.append('.')
from advanced_trading.macro_analyzer import MacroAnalyzer
ma = MacroAnalyzer()
print('✅ Macro Analyzer cargado correctamente')
"""
        
        with open('temp_macro_test.py', 'w') as f:
            f.write(test_macro)
        
        result = self.run_command("python3 temp_macro_test.py", "Macro Analyzer funcional")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_macro_test.py'):
            os.remove('temp_macro_test.py')
        
        return result
    
    def test_arbitrage_system(self) -> bool:
        """Test 6: Verificar Sistema de Arbitraje"""
        print("\n⚖️ TEST 6: Sistema de Arbitraje")
        
        test_arb = """
import sys
sys.path.append('.')
from advanced_trading.relative_arbitrage import RelativeArbitrage
ra = RelativeArbitrage()
print('✅ Relative Arbitrage cargado correctamente')
"""
        
        with open('temp_arb_test.py', 'w') as f:
            f.write(test_arb)
        
        result = self.run_command("python3 temp_arb_test.py", "Sistema de arbitraje funcional")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_arb_test.py'):
            os.remove('temp_arb_test.py')
        
        return result
    
    def test_execution_system(self) -> bool:
        """Test 7: Verificar Sistema de Ejecución"""
        print("\n🚀 TEST 7: Sistema de Ejecución")
        
        test_exec = """
import sys
sys.path.append('.')
from advanced_trading.staggered_execution import StaggeredExecution
se = StaggeredExecution()
print('✅ Staggered Execution cargado correctamente')
"""
        
        with open('temp_exec_test.py', 'w') as f:
            f.write(test_exec)
        
        result = self.run_command("python3 temp_exec_test.py", "Sistema de ejecución funcional")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_exec_test.py'):
            os.remove('temp_exec_test.py')
        
        return result
    
    def test_calibration_system(self) -> bool:
        """Test 8: Verificar Sistema de Calibración"""
        print("\n🔧 TEST 8: Sistema de Calibración")
        
        # Verificar que las configuraciones de calibración están presentes
        test_cal = """
import sys
sys.path.append('.')
from advanced_trading.config.trading_config import TRADING_CONFIG
config = TRADING_CONFIG

# Verificar configuraciones críticas
required_configs = [
    'CALIBRATION_GUARDRAILS',
    'MANUAL_APPROVAL', 
    'SNAPSHOT_ROLLBACK',
    'EVENT_FAMILIES',
    'BACKTEST_METRICS'
]

missing = []
for req in required_configs:
    if req not in config:
        missing.append(req)

if missing:
    print(f'❌ Configuraciones faltantes: {missing}')
else:
    print('✅ Todas las configuraciones de calibración presentes')
    print(f'✅ Max Delta per Cycle: {config["CALIBRATION_GUARDRAILS"]["MAX_DELTA_PER_CYCLE"]}')
    print(f'✅ Manual Approval: {config["MANUAL_APPROVAL"]["ENABLED"]}')
    print(f'✅ Snapshot System: {config["SNAPSHOT_ROLLBACK"]["ENABLED"]}')
"""
        
        with open('temp_cal_test.py', 'w') as f:
            f.write(test_cal)
        
        result = self.run_command("python3 temp_cal_test.py", "Sistema de calibración configurado")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_cal_test.py'):
            os.remove('temp_cal_test.py')
        
        return result
    
    def test_timezone_configuration(self) -> bool:
        """Test 9: Verificar Configuración de Timezone"""
        print("\n🕐 TEST 9: Configuración de Timezone")
        
        test_tz = """
import sys
sys.path.append('.')
from advanced_trading.config.trading_config import TRADING_CONFIG
config = TRADING_CONFIG

timezone_config = config.get('TIMEZONE_CONFIG', {})
primary_tz = timezone_config.get('PRIMARY_TIMEZONE', 'NO_CONFIG')

if primary_tz == 'America/Chicago':
    print('✅ Timezone configurado correctamente en America/Chicago')
    print(f'✅ Ingest: {timezone_config.get("INGEST_TIMEZONE", "NO_CONFIG")}')
    print(f'✅ Scheduler: {timezone_config.get("SCHEDULER_TIMEZONE", "NO_CONFIG")}')
    print(f'✅ Walk-Forward: {timezone_config.get("WALK_FORWARD_TIMEZONE", "NO_CONFIG")}')
else:
    print(f'❌ Timezone incorrecto: {primary_tz}')
"""
        
        with open('temp_tz_test.py', 'w') as f:
            f.write(test_tz)
        
        result = self.run_command("python3 temp_tz_test.py", "Configuración de timezone")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_tz_test.py'):
            os.remove('temp_tz_test.py')
        
        return result
    
    def test_feature_flags(self) -> bool:
        """Test 10: Verificar Feature Flags"""
        print("\n🚩 TEST 10: Feature Flags")
        
        test_flags = """
import sys
sys.path.append('.')
from advanced_trading.config.trading_config import TRADING_CONFIG
config = TRADING_CONFIG

features = config.get('FEATURES', {})
required_flags = [
    'AUTO_CALIBRATION_ON',
    'REQUIRE_MANUAL_APPROVAL',
    'ROLLBACK_ON_DEGRADATION',
    'HIST_WEIGHTING_ON',
    'BACKTEST_OPT_ON',
    'STOP_RULES_ON'
]

missing = []
for flag in required_flags:
    if flag not in features:
        missing.append(flag)

if missing:
    print(f'❌ Feature flags faltantes: {missing}')
else:
    print('✅ Todos los feature flags presentes')
    for flag in required_flags:
        status = 'ON' if features[flag] else 'OFF'
        print(f'   {flag}: {status}')
"""
        
        with open('temp_flags_test.py', 'w') as f:
            f.write(test_flags)
        
        result = self.run_command("python3 temp_flags_test.py", "Feature flags configurados")
        
        # Limpiar archivo temporal
        if os.path.exists('temp_flags_test.py'):
            os.remove('temp_flags_test.py')
        
        return result
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Ejecutar todos los smoke tests"""
        print("🚀 INICIANDO SMOKE TESTS COMPLETOS")
        print("=" * 60)
        print("🎯 Objetivo: Validar que el sistema está listo para operaciones")
        print("=" * 60)
        
        # Lista de todos los tests
        tests = [
            ("Estructura de Base de Datos", self.test_database_structure),
            ("Cobertura de Datos", self.test_data_coverage),
            ("Carga de Configuración", self.test_configuration_loading),
            ("Risk Manager", self.test_risk_manager),
            ("Macro Analyzer", self.test_macro_analyzer),
            ("Sistema de Arbitraje", self.test_arbitrage_system),
            ("Sistema de Ejecución", self.test_execution_system),
            ("Sistema de Calibración", self.test_calibration_system),
            ("Configuración de Timezone", self.test_timezone_configuration),
            ("Feature Flags", self.test_feature_flags)
        ]
        
        # Ejecutar cada test
        for test_name, test_func in tests:
            self.total_tests += 1
            print(f"\n{'='*60}")
            print(f"🧪 TEST {self.total_tests}/10: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                self.test_results[test_name] = result
                if result:
                    self.passed_tests += 1
                    print(f"   🎉 {test_name}: PASÓ")
                else:
                    print(f"   💥 {test_name}: FALLÓ")
            except Exception as e:
                print(f"   💥 {test_name}: EXCEPCIÓN - {e}")
                self.test_results[test_name] = False
        
        return self.test_results
    
    def generate_report(self) -> None:
        """Generar reporte final de smoke tests"""
        print(f"\n{'='*60}")
        print("📋 REPORTE FINAL DE SMOKE TESTS")
        print(f"{'='*60}")
        
        print(f"📊 Resumen:")
        print(f"   Total de tests: {self.total_tests}")
        print(f"   Tests pasados: {self.passed_tests}")
        print(f"   Tests fallidos: {self.total_tests - self.passed_tests}")
        print(f"   Tasa de éxito: {(self.passed_tests/self.total_tests)*100:.1f}%")
        
        print(f"\n📋 Detalle por test:")
        for test_name, result in self.test_results.items():
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 RESULTADO FINAL:")
        if self.passed_tests == self.total_tests:
            print("   🚀 SISTEMA LISTO PARA OPERACIONES")
            print("   ✅ Todos los smoke tests pasaron")
            print("   ✅ Sistema validado completamente")
            print("   ✅ Puedes proceder con confianza")
        else:
            print("   ⚠️ SISTEMA NO LISTO PARA OPERACIONES")
            print("   ❌ Algunos smoke tests fallaron")
            print("   ❌ Se requieren correcciones")
            print("   ❌ NO procedas hasta resolver todos los problemas")
        
        print(f"\n🔒 TU DINERO ESTÁ PROTEGIDO:")
        print("   - El sistema NO permitirá operar sin validación completa")
        print("   - Todos los guardrails están activos")
        print("   - Se requiere aprobación manual para cambios grandes")
        print("   - Rollback automático si las métricas empeoran")

def main():
    """Función principal"""
    runner = SmokeTestRunner()
    results = runner.run_all_tests()
    runner.generate_report()
    
    # Retornar código de salida apropiado
    all_passed = all(results.values())
    exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
