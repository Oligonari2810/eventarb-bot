import os
import sqlite3
import logging
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

def finalize_trade_with_fees(trade_id: int, exit_price: Decimal, 
                            db_path: str = "trades.db") -> bool:
    """Finalize trade with commission calculation"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get trade details
            cursor.execute("""
                SELECT entry_price, quantity, side, notional_usd 
                FROM trades WHERE id = ?
            """, (trade_id,))
            
            result = cursor.fetchone()
            if not result:
                logger.error(f"Trade {trade_id} not found")
                return False
                
            entry_price, quantity, side, notional_usd = result
            
            # Calculate PnL
            if side == "BUY":
                pnl = (exit_price - entry_price) * quantity
            else:  # SELL
                pnl = (entry_price - exit_price) * quantity
            
            # Calculate commission (default 0.1% = 10 bps)
            fee_rate = float(os.getenv("FEE_RATE_BPS", "10")) / 10000.0
            notional = abs(exit_price * quantity)
            fee = notional * fee_rate
            pnl_net = pnl - fee
            
            # Update trade
            cursor.execute("""
                UPDATE trades 
                SET exit_price = ?,
                    pnl_usd = ?,
                    pnl_fee_usd = ?,
                    pnl_net_usd = ?,
                    closed_at = ?,
                    status = 'CLOSED'
                WHERE id = ?
            """, (float(exit_price), float(pnl), float(fee), 
                  float(pnl_net), datetime.utcnow().isoformat(), trade_id))
            
            conn.commit()
            
            logger.info(f"✅ Trade {trade_id} closed: PnL=${pnl:.4f}, Fee=${fee:.4f}, Net=${pnl_net:.4f}")
            return True
            
    except Exception as e:
        logger.error(f"Error finalizing trade {trade_id}: {e}")
        return False

def today_loss_pct_with_fees(db_path: str = "trades.db") -> float:
    """Calculate today's loss percentage including fees"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            
            # Use pnl_net_usd if available, fallback to pnl_usd
            cursor.execute("""
                SELECT COALESCE(SUM(COALESCE(pnl_net_usd, pnl_usd)), 0.0) as total_pnl,
                       SUM(notional_usd) as total_notional
                FROM trades 
                WHERE date(created_at) = ? AND status = 'CLOSED'
            """, (today,))
            
            result = cursor.fetchone()
            if not result or result[1] is None or result[1] == 0:
                return 0.0
                
            total_pnl, total_notional = result
            if total_notional and total_notional > 0:
                return (total_pnl / total_notional) * 100
            return 0.0
            
    except Exception as e:
        logger.error(f"Error calculating today's loss percentage: {e}")
        return 0.0
