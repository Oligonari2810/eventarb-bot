#!/usr/bin/env python3
import datetime
import sqlite3
import sys
import os

# Agregar el directorio raíz al path para importar eventarb
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eventarb.utils.notify import send_telegram

def generate_daily_report():
    """Genera reporte diario de trading"""
    today = datetime.datetime.utcnow().date().isoformat()
    
    try:
        conn = sqlite3.connect('trades.db')
        cursor = conn.cursor()
        
        # Métricas del día
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl_usd <= 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl_usd) as total_pnl,
                AVG(pnl_usd) as avg_pnl
            FROM trades 
            WHERE DATE(created_at) = ?
        """, (today,))
        
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total, wins, losses, pnl, avg_pnl = result
            win_rate = (wins / total) * 100 if total > 0 else 0
            
            message = (
                f"📊 *Reporte Diario - {today}*\n"
                f"• Trades: {total}\n"
                f"• Wins: {wins} | Losses: {losses}\n"
                f"• Win Rate: {win_rate:.1f}%\n"
                f"• PnL: ${pnl:.2f}\n"
                f"• Avg Trade: ${avg_pnl:.2f}"
            )
        else:
            message = f"📊 *Reporte Diario - {today}*\nNo hay trades hoy"
            
        send_telegram(message)
        conn.close()
        
    except Exception as e:
        send_telegram(f"❌ *Error en Reporte*\n{str(e)}")

if __name__ == "__main__":
    generate_daily_report()
