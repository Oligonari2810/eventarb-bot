#!/usr/bin/env python3
"""
Script principal del Trading Engine con validaciones de seguridad completas
Solo permite operaciones después de validación completa del sistema
"""

import sys
import os
import argparse
from datetime import datetime
import pytz

def check_system_readiness():
    """Verificar que el sistema esté listo para operaciones"""
    print("🔒 VERIFICANDO READINESS DEL SISTEMA...")
    
    # Verificar que existe la BD
    if not os.path.exists('trading_data.db'):
        print("❌ Base de datos no encontrada")
        return False
    
    # Verificar cobertura de datos
    try:
        import subprocess
        result = subprocess.run(['python3', 'validate_data_coverage.py'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Validación de cobertura falló")
            return False
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False
    
    print("✅ Sistema verificado y listo")
    return True

def main():
    parser = argparse.ArgumentParser(description='Trading Engine Principal')
    parser.add_argument('--dry-run', action='store_true', help='Ejecutar en modo simulación')
    parser.add_argument('--validate-only', action='store_true', help='Solo validar sistema')
    
    args = parser.parse_args()
    
    print("🚀 TRADING ENGINE - SISTEMA DE SEGURIDAD ACTIVO")
    print("=" * 60)
    
    # Verificar readiness
    if not check_system_readiness():
        print("❌ SISTEMA NO LISTO - ABORTANDO")
        sys.exit(1)
    
    if args.validate_only:
        print("✅ Validación completada - Sistema listo")
        return
    
    # Modo dry-run por defecto
    if args.dry_run:
        print("🧪 MODO DRY-RUN ACTIVADO - Sin operaciones reales")
    else:
        print("⚠️ MODO PRODUCCIÓN - Requiere aprobación manual")
        response = input("¿Continuar con operaciones reales? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operación cancelada por el usuario")
            return
    
    print("🎯 Iniciando trading engine...")
    # Aquí iría la lógica principal del trading

if __name__ == "__main__":
    main()
