#!/usr/bin/env python3
"""
Sistema de ejecución escalonada para mejor execution quality
Implementación completa según especificaciones de DS
"""

import asyncio
from typing import Dict, List, Any
import time
import numpy as np

class StaggeredExecution:
    def __init__(self, volatility_adjustment: bool = True):
        self.volatility_adjustment = volatility_adjustment
        self.execution_history = []
        
    def generate_execution_plan(self, signal: str, total_amount: float, 
                              volatility_factor: float = 1.0) -> List[Dict[str, Any]]:
        """
        Genera plan de ejecución escalonada
        """
        # Ajustar por volatilidad
        size_multiplier = min(1.0, 1.0 / volatility_factor) if volatility_factor > 1.0 else 1.0
        
        execution_plan = [
            {
                'stage': 'T0',
                'amount': total_amount * 0.15 * size_multiplier,
                'conditions': None,
                'description': 'Entrada inicial inmediata',
                'time_delay': 0
            },
            {
                'stage': 'T+30s',
                'amount': total_amount * 0.30 * size_multiplier,
                'conditions': ['price_confirmation', 'volume_spike'],
                'description': 'Segunda entrada con confirmación',
                'time_delay': 30
            },
            {
                'stage': 'T+2min', 
                'amount': total_amount * 0.55 * size_multiplier,
                'conditions': ['trend_confirmation', 'volatility_decrease'],
                'description': 'Entrada final con confirmación de tendencia',
                'time_delay': 120
            }
        ]
        
        return execution_plan
    
    async def execute_plan(self, plan: List[Dict[str, Any]], symbol: str, signal: str):
        """
        Ejecuta el plan de trading escalonado
        """
        executed_orders = []
        
        for stage in plan:
            # Esperar el delay apropiado
            if stage['time_delay'] > 0:
                await asyncio.sleep(stage['time_delay'])
            
            # Verificar condiciones si existen
            if stage['conditions']:
                market_data = await self._get_market_data(symbol)
                if not self._check_conditions(stage['conditions'], market_data, signal):
                    print(f"❌ Condiciones no cumplidas para {stage['stage']}. Saltando etapa.")
                    continue
            
            # Ejecutar orden (simulado - integrar con API real)
            order = await self._place_order(
                symbol=symbol,
                side=signal.lower(),
                amount=stage['amount'],
                order_type='market'
            )
            
            executed_orders.append({
                'stage': stage['stage'],
                'order': order,
                'amount': stage['amount'],
                'timestamp': time.time()
            })
            
            print(f"✅ Ejecutado {stage['stage']}: {stage['amount']} {symbol}")
        
        return executed_orders
    
    async def _get_market_data(self, symbol: str) -> Dict:
        """Obtiene data de mercado (simulado - integrar con API real)"""
        # Simulación - en producción conectar con API de exchange
        return {
            'price_change_pct': 0.002,  # +0.2%
            'volume': 1000000,
            'avg_volume': 800000,
            'volatility': 0.015,
            'spread': 0.0001  # 1bps
        }
    
    def _check_conditions(self, conditions: List[str], market_data: Dict, signal: str) -> bool:
        """Verifica condiciones de ejecución"""
        checks = []
        
        for condition in conditions:
            if condition == 'price_confirmation':
                # Precio se mueve en dirección esperada
                price_move = market_data.get('price_change_pct', 0)
                expected_direction = 1 if signal == 'BUY' else -1
                checks.append(price_move * expected_direction > 0.001)
                
            elif condition == 'volume_spike':
                # Volumen 50% above average
                current_volume = market_data.get('volume', 0)
                avg_volume = market_data.get('avg_volume', current_volume)
                checks.append(current_volume > avg_volume * 1.5)
                
            elif condition == 'trend_confirmation':
                # Trend continues in expected direction
                checks.append(True)  # Simulación siempre true
                
            elif condition == 'volatility_decrease':
                # Volatility decreases after initial spike
                current_vol = market_data.get('volatility', 0)
                initial_vol = market_data.get('initial_volatility', current_vol)
                checks.append(current_vol < initial_vol * 0.7)
        
        return all(checks)
    
    async def _place_order(self, symbol: str, side: str, amount: float, order_type: str) -> Dict:
        """Place order (simulado - integrar con API real)"""
        # Simulación - en producción conectar con API de exchange
        return {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'type': order_type,
            'status': 'filled',
            'timestamp': time.time(),
            'simulated': True  # Indicador de orden simulada
        }
    
    def get_execution_metrics(self) -> Dict:
        """Retorna métricas de performance de la ejecución"""
        if not self.execution_history:
            return {}
        
        total_orders = len(self.execution_history)
        successful_stages = len([e for e in self.execution_history if e.get('order', {}).get('status') == 'filled'])
        
        return {
            'total_execution_plans': len(set([e.get('plan_id', 0) for e in self.execution_history])),
            'total_orders_placed': total_orders,
            'successful_executions': successful_stages,
            'execution_success_rate': successful_stages / total_orders if total_orders > 0 else 0,
            'avg_execution_time': np.mean([e.get('execution_time', 0) for e in self.execution_history]) if self.execution_history else 0
        }
    
    def add_execution_record(self, plan_id: str, stage: str, amount: float, 
                           execution_time: float, success: bool):
        """Agrega registro de ejecución para métricas"""
        self.execution_history.append({
            'plan_id': plan_id,
            'stage': stage,
            'amount': amount,
            'execution_time': execution_time,
            'success': success,
            'timestamp': time.time()
        })

def generate_staggered_plan(signal: str, total_amount: float, 
                          volatility_factor: float = 1.0) -> List[Dict[str, Any]]:
    """
    Función de conveniencia para generar plan de ejecución
    """
    executor = StaggeredExecution()
    return executor.generate_execution_plan(signal, total_amount, volatility_factor)

async def execute_staggered_plan(plan: List[Dict[str, Any]], symbol: str, signal: str):
    """
    Función de conveniencia para ejecutar plan de ejecución
    """
    executor = StaggeredExecution()
    return await executor.execute_plan(plan, symbol, signal)
