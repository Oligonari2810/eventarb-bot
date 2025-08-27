#!/usr/bin/env python3
"""
Motor de arbitraje relativo entre pares de criptos
Implementación completa según especificaciones de DS
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

class RelativeArbitrage:
    def __init__(self, correlation_threshold: float = 0.7, divergence_threshold: float = 0.01):
        self.correlation_threshold = correlation_threshold
        self.divergence_threshold = divergence_threshold
        self.price_history = {'BTC/USDT': [], 'ETH/USDT': []}
        
    def update_prices(self, btc_price: float, eth_price: float):
        """Actualiza historial de precios"""
        self.price_history['BTC/USDT'].append(btc_price)
        self.price_history['ETH/USDT'].append(eth_price)
        
        # Mantener sólo últimas 100 observaciones
        for symbol in self.price_history:
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
    
    def check_arbitrage_opportunity(self, lookback_period: int = 30) -> Optional[Dict]:
        """
        Detecta oportunidades de arbitraje entre BTC/ETH
        """
        if len(self.price_history['BTC/USDT']) < lookback_period:
            return None
            
        btc_prices = self.price_history['BTC/USDT'][-lookback_period:]
        eth_prices = self.price_history['ETH/USDT'][-lookback_period:]
        
        correlation = self._calculate_correlation(btc_prices, eth_prices)
        
        if correlation < self.correlation_threshold:
            return None
            
        # Calcular rendimientos recientes
        btc_return = (btc_prices[-1] - btc_prices[0]) / btc_prices[0]
        eth_return = (eth_prices[-1] - eth_prices[0]) / eth_prices[0]
        divergence = abs(btc_return - eth_return)
        
        if divergence > self.divergence_threshold:
            signal = 'LONG_ETH_SHORT_BTC' if btc_return > eth_return else 'LONG_BTC_SHORT_ETH'
            
            return {
                'signal': signal,
                'correlation': correlation,
                'divergence': divergence,
                'btc_return': btc_return,
                'eth_return': eth_return,
                'timestamp': len(self.price_history['BTC/USDT'])
            }
        
        return None
    
    def _calculate_correlation(self, prices1: List[float], prices2: List[float]) -> float:
        """Calcula correlación entre dos series de precios"""
        if len(prices1) != len(prices2) or len(prices1) < 2:
            return 0.0
        
        returns1 = np.diff(prices1) / prices1[:-1]
        returns2 = np.diff(prices2) / prices2[:-1]
        
        if len(returns1) == 0 or len(returns2) == 0:
            return 0.0
            
        correlation = np.corrcoef(returns1, returns2)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def calculate_position_sizes(self, btc_price: float, eth_price: float, 
                               capital: float, risk_pct: float = 0.01) -> Tuple[float, float]:
        """Calcula tamaños de posición para arbitraje"""
        hedge_ratio = btc_price / eth_price
        risk_amount = capital * risk_pct
        
        # Asumir máximo drawdown de 2% en el spread
        btc_size = risk_amount / (0.02 * btc_price)
        eth_size = btc_size * hedge_ratio
        
        return btc_size, eth_size
    
    def get_arbitrage_metrics(self) -> Dict:
        """Retorna métricas de performance del arbitraje"""
        if len(self.price_history['BTC/USDT']) < 2:
            return {}
        
        btc_returns = np.diff(self.price_history['BTC/USDT']) / self.price_history['BTC/USDT'][:-1]
        eth_returns = np.diff(self.price_history['ETH/USDT']) / self.price_history['ETH/USDT'][:-1]
        
        correlation = self._calculate_correlation(self.price_history['BTC/USDT'], self.price_history['ETH/USDT'])
        
        return {
            'total_observations': len(self.price_history['BTC/USDT']),
            'current_correlation': correlation,
            'btc_volatility': np.std(btc_returns) if len(btc_returns) > 0 else 0,
            'eth_volatility': np.std(eth_returns) if len(eth_returns) > 0 else 0,
            'correlation_threshold': self.correlation_threshold,
            'divergence_threshold': self.divergence_threshold
        }
    
    def reset_history(self):
        """Resetea el historial de precios"""
        self.price_history = {'BTC/USDT': [], 'ETH/USDT': []}
    
    def set_thresholds(self, correlation_threshold: float, divergence_threshold: float):
        """Actualiza los umbrales de detección"""
        self.correlation_threshold = correlation_threshold
        self.divergence_threshold = divergence_threshold
