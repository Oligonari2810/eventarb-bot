import logging
from decimal import Decimal
from eventarb.exec.binance_client import build_binance_client

logger = logging.getLogger("eventarb")

class OrderRouter:
    def __init__(self, simulation=True):
        self.simulation = simulation
        self.client = None if simulation else build_binance_client()
    
    def place_market_paper(self, symbol: str, side: str, notional_usd: Decimal, 
                          last_price: Decimal) -> dict:
        """Simulate market order execution (paper trading)"""
        # Calculate quantity
        quantity = notional_usd / last_price
        quantity = round(quantity, 6)  # Binance precision
        
        fill_price = last_price
        
        logger.info(f"✅ PAPER fill: {symbol} {side} qty={quantity} @ {fill_price}")
        
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "fill_price": float(fill_price),
            "notional_usd": float(notional_usd),
            "simulated": True
        }
    
    def place_market_real(self, symbol: str, side: str, notional_usd: Decimal, 
                         last_price: Decimal) -> dict:
        """Execute real market order on Binance mainnet"""
        if self.simulation:
            return self.place_market_paper(symbol, side, notional_usd, last_price)
        
        try:
            # Calculate quantity
            quantity = notional_usd / last_price
            quantity = round(quantity, 6)  # Binance precision
            
            # Place real market order
            order = self.client.order_market(
                symbol=symbol,
                side=side,
                quantity=quantity
            )
            
            logger.info(f"✅ REAL fill: {symbol} {side} qty={quantity} @ {last_price} | OrderID: {order['orderId']}")
            
            return {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "fill_price": float(last_price),
                "notional_usd": float(notional_usd),
                "simulated": False,
                "order_id": order['orderId'],
                "status": order['status']
            }
            
        except Exception as e:
            logger.error(f"❌ Error placing real order: {e}")
            raise

