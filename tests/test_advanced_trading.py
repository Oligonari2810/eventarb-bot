"""
Tests de integración para el sistema de trading avanzado
"""
import unittest
from advanced_trading.macro_analyzer import consensus_vs_actual, calculate_deviation_percentage
from advanced_trading.staggered_execution import generate_staggered_plan
from advanced_trading.advanced_risk_manager import calculate_dynamic_sl, generate_tp_targets
from advanced_trading.relative_arbitrage import check_arbitrage_opportunity

class TestAdvancedTrading(unittest.TestCase):
    
    def test_consensus_vs_actual(self):
        # Test CPI scenarios
        self.assertEqual(consensus_vs_actual('CPI', 3.2, 3.5), 'SELL')
        self.assertEqual(consensus_vs_actual('CPI', 3.2, 3.0), 'BUY')
        self.assertEqual(consensus_vs_actual('CPI', 3.2, 3.2), 'STAY')
        
        # Test GDP scenarios
        self.assertEqual(consensus_vs_actual('GDP', 2.1, 1.8), 'BUY')
        self.assertEqual(consensus_vs_actual('GDP', 2.1, 2.4), 'SELL')
    
    def test_deviation_calculation(self):
        self.assertAlmostEqual(calculate_deviation_percentage(100, 105), 5.0)
        self.assertAlmostEqual(calculate_deviation_percentage(100, 95), -5.0)
    
    def test_staggered_execution(self):
        plan = generate_staggered_plan('BUY', 10000)
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]['amount'], 4000)  # 40% (TP_ALLOCATION[0])
        self.assertEqual(plan[1]['amount'], 3500)  # 35% (TP_ALLOCATION[1])
        self.assertEqual(plan[2]['amount'], 2500)  # 25% (TP_ALLOCATION[2])
    
    def test_dynamic_sl(self):
        sl = calculate_dynamic_sl(0.02, 0.001)  # ATR 2%, spread 0.1%
        self.assertAlmostEqual(sl, 0.04)  # max(4%, 0.3%) = 4%
    
    def test_arbitrage_opportunity(self):
        # Datos que cumplan umbrales: correlación alta + divergencia > 1%
        btc_prices = [50000, 50100, 50200, 50300, 50400, 50500]  # +1%
        eth_prices = [3000, 3000, 3000, 3000, 3000, 3000]       # 0%
        
        # Usar lookback=5 y verificar que los datos cumplan los requisitos
        signal = check_arbitrage_opportunity(btc_prices, eth_prices, lookback_period=5)
        
        # Verificar que la correlación sea alta y la divergencia > 1%
        # BTC: +1% en 5 períodos, ETH: 0% → divergencia = 1% (umbral mínimo)
        self.assertIsNotNone(signal, "Debería detectar oportunidad con divergencia = 1%")
        self.assertIn(signal, ['long_eth_short_btc', 'long_btc_short_eth'])

if __name__ == '__main__':
    unittest.main()
