"""
Sistema avanzado de gestión de riesgo institucional
Stop loss dinámico, take profit escalonado, y límites de exposición
"""
import numpy as np
from typing import List, Tuple

def calculate_dynamic_sl(atr: float, current_spread: float, volatility_factor: float = 1.0) -> float:
    """
    Calcula stop loss dinámico basado en ATR y spread
    
    Args:
        atr: Average True Range (volatilidad)
        current_spread: Spread actual del mercado
        volatility_factor: Multiplicador de volatilidad (1.0 = normal)
    
    Returns:
        Stop loss distance in percentage
    """
    # SL = máximo entre 2*ATR y 3*spread, ajustado por volatilidad
    atr_sl = atr * 2 * volatility_factor
    spread_sl = current_spread * 3 * volatility_factor
    return max(atr_sl, spread_sl)

def generate_tp_targets(entry_price: float, direction: int, 
                       volatility_factor: float = 1.0) -> List[float]:
    """
    Genera objetivos de take profit escalonados
    
    Args:
        entry_price: Precio de entrada
        direction: 1 para LONG, -1 para SHORT
        volatility_factor: Ajuste por volatilidad
    
    Returns:
        Lista de precios objetivo para TP
    """
    # Usar TP_LEVELS y TP_ALLOCATION de la nueva configuración
    base_levels = [0.005, 0.01, 0.02]  # 0.5%, 1%, 2%
    
    # Adjust for volatility
    adjusted_levels = [level * volatility_factor for level in base_levels]
    
    # Calculate target prices
    targets = []
    for level in adjusted_levels:
        target_price = entry_price * (1 + level * direction)
        targets.append(round(target_price, 2))
    
    return targets

def calculate_position_size(account_balance: float, risk_per_trade: float,
                          entry_price: float, stop_loss: float) -> float:
    """
    Calcula el tamaño de posición basado en riesgo por trade
    
    Args:
        account_balance: Balance total de la cuenta
        risk_per_trade: Riesgo por trade (ej: 0.01 para 1%)
        entry_price: Precio de entrada
        stop_loss: Precio de stop loss
    
    Returns:
        Tamaño de posición en unidades
    """
    risk_amount = account_balance * risk_per_trade
    risk_per_unit = abs(entry_price - stop_loss)
    
    if risk_per_unit == 0:
        return 0.0
    
    return risk_amount / risk_per_unit

def check_daily_limits(daily_pnl: float, daily_trades: int, 
                      max_daily_loss: float = 0.05, 
                      max_daily_trades: int = 10) -> Tuple[bool, str]:
    """
    Verifica límites diarios de trading
    
    Returns:
        (is_ok, message)
    """
    if daily_pnl <= -max_daily_loss:
        return False, f"Daily loss limit reached: {daily_pnl:.2%}"
    
    if daily_trades >= max_daily_trades:
        return False, f"Daily trade limit reached: {daily_trades}"
    
    return True, "Within limits"

class AdvancedRiskManager:
    """Gestor avanzado de riesgo con state management"""
    
    def __init__(self, account_balance: float, risk_per_trade: float = 0.015):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.open_positions = []
    
    def update_daily_stats(self, pnl_change: float, trades: int = 1):
        """Actualiza estadísticas diarias"""
        self.daily_pnl += pnl_change
        self.daily_trades += trades
    
    def can_trade(self) -> Tuple[bool, str]:
        """Verifica si se puede realizar otro trade"""
        return check_daily_limits(self.daily_pnl, self.daily_trades)
    
    def calculate_trade_parameters(self, symbol: str, entry_price: float,
                                 atr: float, spread: float) -> dict:
        """Calcula todos los parámetros para un trade"""
        sl_distance = calculate_dynamic_sl(atr, spread)
        sl_price = entry_price * (1 - sl_distance) if entry_price > 0 else 0
        
        position_size = calculate_position_size(
            self.account_balance, self.risk_per_trade, entry_price, sl_price
        )
        
        tp_prices = generate_tp_targets(entry_price, 1)  # Assuming long for calculation
        
        return {
            'position_size': position_size,
            'stop_loss': sl_price,
            'take_profits': tp_prices,
            'risk_reward_ratio': (tp_prices[0] - entry_price) / (entry_price - sl_price)
        }
