import logging
import sys
import os
from decimal import Decimal

# Agregar el directorio raíz al path para importar funciones de app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from eventarb.exec.binance_client import build_binance_client

logger = logging.getLogger("eventarb")


class OrderRouter:
    def __init__(self, simulation=True):
        self.simulation = simulation
        self.client = None if simulation else build_binance_client()

    def _validate_and_adjust_quantity(
        self, symbol: str, quantity: float, price: float
    ) -> tuple[bool, str, float]:
        """
        Valida y ajusta la cantidad para cumplir con el notional mínimo de Binance.
        Retorna: (es_válida, mensaje, cantidad_ajustada)
        """
        try:
            # Importar funciones de validación de app.py
            from app import validate_order_parameters

            is_valid, message, adjusted_quantity = validate_order_parameters(
                symbol, "BUY", quantity, price
            )

            if is_valid and adjusted_quantity != quantity:
                logger.warning(f"🔄 {message}")
                return True, message, adjusted_quantity

            return is_valid, message, adjusted_quantity

        except ImportError:
            # Fallback si no se puede importar app.py
            logger.warning(
                "⚠️  No se pudo importar validación de app.py, usando validación básica"
            )
            return self._basic_validation(symbol, quantity, price)
        except Exception as e:
            logger.error(f"❌ Error en validación: {e}")
            return False, f"Error de validación: {e}", 0.0

    def _basic_validation(
        self, symbol: str, quantity: float, price: float
    ) -> tuple[bool, str, float]:
        """
        Validación básica de notional como fallback
        """
        notional = quantity * price
        if notional < 10.0:
            # Ajustar cantidad para cumplir notional mínimo
            adjusted_quantity = (10.0 / price) * 1.001  # +0.1% margen
            adjusted_quantity = round(adjusted_quantity, 8)
            return (
                True,
                f"Quantity ajustada para cumplir notional mínimo: {adjusted_quantity}",
                adjusted_quantity,
            )

        return True, "Validación básica exitosa", quantity

    def place_market_paper(
        self, symbol: str, side: str, notional_usd: Decimal, last_price: Decimal
    ) -> dict:
        """Simulate market order execution (paper trading)"""
        # Calculate quantity
        quantity = notional_usd / last_price
        quantity = round(quantity, 6)  # Binance precision

        # Validar y ajustar cantidad si es necesario
        is_valid, message, adjusted_quantity = self._validate_and_adjust_quantity(
            symbol, float(quantity), float(last_price)
        )

        if not is_valid:
            logger.error(f"❌ PAPER order validation failed: {message}")
            raise ValueError(f"Order validation failed: {message}")

        if adjusted_quantity != float(quantity):
            logger.info(f"🔄 PAPER quantity adjusted: {quantity} → {adjusted_quantity}")
            quantity = Decimal(str(adjusted_quantity))

        fill_price = last_price

        logger.info(f"✅ PAPER fill: {symbol} {side} qty={quantity} @ {fill_price}")

        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "fill_price": float(fill_price),
            "notional_usd": float(notional_usd),
            "simulated": True,
        }

    def place_market_real(
        self, symbol: str, side: str, notional_usd: Decimal, last_price: Decimal
    ) -> dict:
        """Execute real market order on Binance mainnet"""
        if self.simulation:
            return self.place_market_paper(symbol, side, notional_usd, last_price)

        try:
            # Calculate quantity
            quantity = notional_usd / last_price
            quantity = round(quantity, 6)  # Binance precision

            # Validar y ajustar cantidad antes de enviar a Binance
            is_valid, message, adjusted_quantity = self._validate_and_adjust_quantity(
                symbol, float(quantity), float(last_price)
            )

            if not is_valid:
                logger.error(f"❌ REAL order validation failed: {message}")
                raise ValueError(f"Order validation failed: {message}")

            if adjusted_quantity != float(quantity):
                logger.info(
                    f"🔄 REAL quantity adjusted: {quantity} → {adjusted_quantity}"
                )
                quantity = adjusted_quantity

            # Place real market order with validated quantity
            order = self.client.order_market(
                symbol=symbol, side=side, quantity=quantity
            )

            logger.info(
                f"✅ REAL fill: {symbol} {side} qty={quantity} @ {last_price} | OrderID: {order['orderId']}"
            )

            return {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "fill_price": float(last_price),
                "notional_usd": float(notional_usd),
                "simulated": False,
                "order_id": order["orderId"],
                "status": order["status"],
            }

        except Exception as e:
            logger.error(f"❌ Error placing real order: {e}")
            raise
