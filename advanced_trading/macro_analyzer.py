#!/usr/bin/env python3
"""
Analyzer institucional para eventos macroeconómicos
Implementación completa según especificaciones de DS
"""

from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

class MacroAnalyzer:
    def __init__(self, impact_threshold: float = 0.2):
        self.impact_threshold = impact_threshold
        self.event_history = []
        
    def analyze_event(self, event_type: str, consensus: float, actual: float, 
                     previous: Optional[float] = None) -> Dict:
        """
        Analiza evento macro y devuelve señal de trading
        """
        deviation = self._calculate_deviation(consensus, actual)
        impact_score = self._calculate_impact_score(event_type, deviation)
        direction = self._determine_direction(event_type, consensus, actual)
        
        analysis = {
            'event_type': event_type,
            'consensus': consensus,
            'actual': actual,
            'deviation': deviation,
            'deviation_pct': (deviation / consensus * 100) if consensus != 0 else 0,
            'impact_score': impact_score,
            'direction': direction,
            'timestamp': datetime.now().isoformat(),
            'should_trade': impact_score >= self.impact_threshold
        }
        
        self.event_history.append(analysis)
        return analysis
    
    def _calculate_deviation(self, consensus: float, actual: float) -> float:
        """Calcula desviación absoluta"""
        return actual - consensus
    
    def _calculate_impact_score(self, event_type: str, deviation: float) -> float:
        """Calcula score de impacto basado en tipo de evento y desviación"""
        event_weights = {
            'CPI': 0.9, 'GDP': 0.85, 'UNEMPLOYMENT': 0.8,
            'INTEREST_RATE': 0.95, 'RETAIL_SALES': 0.7
        }
        
        base_weight = event_weights.get(event_type, 0.5)
        deviation_impact = min(1.0, abs(deviation) * 2)  # Normalizado
        
        return base_weight * deviation_impact
    
    def _determine_direction(self, event_type: str, consensus: float, actual: float) -> str:
        """Determina dirección de trading basado en reglas macro"""
        event_type = event_type.upper()
        
        if event_type == 'CPI':
            return 'SELL' if actual > consensus else 'BUY'
        elif event_type == 'GDP':
            return 'BUY' if actual < consensus else 'SELL'
        elif event_type == 'UNEMPLOYMENT':
            return 'BUY' if actual > consensus else 'SELL'
        elif event_type == 'INTEREST_RATE':
            return 'SELL' if actual > consensus else 'BUY'
        else:
            return 'HOLD'
    
    def get_performance_metrics(self) -> Dict:
        """Retorna métricas de performance del analyzer"""
        if not self.event_history:
            return {}
            
        successful_trades = [e for e in self.event_history if e['should_trade']]
        hit_rate = len([e for e in successful_trades if self._was_trade_successful(e)]) / len(successful_trades) if successful_trades else 0
        
        return {
            'total_events_analyzed': len(self.event_history),
            'trading_signals_generated': len(successful_trades),
            'estimated_hit_rate': hit_rate,
            'avg_impact_score': np.mean([e['impact_score'] for e in self.event_history]) if self.event_history else 0
        }
    
    def _was_trade_successful(self, event_analysis: Dict) -> bool:
        """Determina si un trade hubiera sido exitoso (simplificado)"""
        # Esta es una simulación - en producción se conectaría con data real
        return event_analysis['impact_score'] > 0.3  # Simulación simple

def consensus_vs_actual(event_type: str, consensus: float, actual: float) -> str:
    """
    Función de conveniencia para análisis rápido
    """
    analyzer = MacroAnalyzer()
    result = analyzer.analyze_event(event_type, consensus, actual)
    return result['direction']

def get_trading_parameters(event_type: str, deviation: float) -> Dict:
    """
    Obtiene parámetros de trading basados en tipo de evento y desviación
    """
    base_params = {
        'size_factor': 1.0,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        'holding_period_minutes': 15
    }
    
    # Ajustar por tipo de evento
    if event_type == 'CPI':
        base_params['size_factor'] = 1.5 if abs(deviation) > 0.1 else 1.0
        base_params['holding_period_minutes'] = 20
    elif event_type == 'GDP':
        base_params['size_factor'] = 2.0 if abs(deviation) > 0.2 else 1.0
        base_params['holding_period_minutes'] = 30
    elif event_type == 'INTEREST_RATE':
        base_params['size_factor'] = 2.5 if abs(deviation) > 0.05 else 1.0
        base_params['holding_period_minutes'] = 45
    
    return base_params
