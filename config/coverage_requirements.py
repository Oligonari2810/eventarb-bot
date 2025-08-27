#!/usr/bin/env python3
"""
Requisitos de cobertura actualizados para período 2023-2024
Implementa la solución propuesta por DS
"""

COVERAGE_REQUIREMENTS = {
    'macro_US': {
        'CPI': {'min_events': 24, 'period': '2023-2024'},
        'GDP': {'min_events': 12, 'period': '2023-2024'},
        'UNEMPLOYMENT': {'min_events': 24, 'period': '2023-2024'},
        'FOMC': {'min_events': 8, 'period': '2023-2024'}
    },
    'macro_EU': {
        'CPI': {'min_events': 15, 'period': '2023-2024'},
        'GDP': {'min_events': 10, 'period': '2023-2024'},
        'ECB_RATE': {'min_events': 15, 'period': '2023-2024'}
    },
    'crypto_events': {
        'UNLOCKS': {'min_events': 50, 'period': '2023-2024'},
        'LISTINGS': {'min_events': 25, 'period': '2023-2024'},
        'SECURITY_INCIDENTS': {'min_events': 10, 'period': '2023-2024'}
    },
    'market_data': {
        'BTC_DAILY': {'min_days': 30, 'period': 'last_30_days'},
        'BOOK_DEPTH': {'min_usd': 2000000, 'period': 'last_7_days'},
        'SPREAD': {'max_bps': 5, 'period': 'last_7_days'}
    }
}

# Configuración de validación
VALIDATION_CONFIG = {
    'date_range': {
        'start': '2023-01-01',
        'end': '2024-12-31',
        'description': 'Período completo 2023-2024'
    },
    'validation_mode': 'fixed_dates',  # Usar fechas específicas, no relativas
    'strict_mode': True,  # Requerir cumplimiento estricto de mínimos
    'auto_adjust': False  # No ajustar automáticamente los mínimos
}

def get_requirement(family: str, event_type: str) -> dict:
    """Obtener requisito específico de cobertura"""
    return COVERAGE_REQUIREMENTS.get(family, {}).get(event_type, {})

def validate_coverage(family: str, event_type: str, actual_count: int) -> bool:
    """Validar si se cumple el requisito de cobertura"""
    requirement = get_requirement(family, event_type)
    if not requirement:
        return False
    
    min_events = requirement.get('min_events', 0)
    return actual_count >= min_events

def get_all_requirements() -> dict:
    """Obtener todos los requisitos de cobertura"""
    return COVERAGE_REQUIREMENTS

if __name__ == "__main__":
    print("📋 Requisitos de cobertura actualizados (2023-2024):")
    for family, events in COVERAGE_REQUIREMENTS.items():
        print(f"\n🏗️ {family}:")
        for event, req in events.items():
            print(f"   {event}: {req['min_events']} eventos en {req['period']}")
    
    print(f"\n⚙️ Configuración de validación:")
    print(f"   Modo: {VALIDATION_CONFIG['validation_mode']}")
    print(f"   Rango de fechas: {VALIDATION_CONFIG['date_range']['start']} a {VALIDATION_CONFIG['date_range']['end']}")
    print(f"   Modo estricto: {VALIDATION_CONFIG['strict_mode']}")
