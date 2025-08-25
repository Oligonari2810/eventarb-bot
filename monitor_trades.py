#!/usr/bin/env python3
"""
Script de monitoreo para EventArb Bot
Muestra métricas clave de trading en tiempo real
"""

import sqlite3
import os
from datetime import datetime, timedelta

def get_db_connection():
    """Conectar a la base de datos"""
    db_path = os.getenv("DB_PATH", "trades.db")
    return sqlite3.connect(db_path)

def get_trades_summary():
    """Obtener resumen de trades por día"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        date(created_at) as fecha,
        COUNT(*) as total_trades,
        ROUND(SUM(notional_usd), 2) as notional_total,
        ROUND(SUM(CASE WHEN pnl_usd > 0 THEN pnl_usd ELSE 0 END), 2) as ganancias,
        ROUND(SUM(CASE WHEN pnl_usd < 0 THEN pnl_usd ELSE 0 END), 2) as perdidas
    FROM trades 
    WHERE created_at IS NOT NULL
    GROUP BY date(created_at) 
    ORDER BY fecha DESC
    LIMIT 7
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_pnl_summary():
    """Obtener resumen de PnL agregado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        date(closed_at) as fecha,
        ROUND(SUM(pnl_usd), 2) as pnl_usd,
        ROUND(100.0 * SUM(pnl_usd) / NULLIF(SUM(notional_usd), 0), 2) as pnl_pct,
        COUNT(*) as trades_cerrados
    FROM trades 
    WHERE closed_at IS NOT NULL
    GROUP BY date(closed_at) 
    ORDER BY fecha DESC
    LIMIT 7
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_win_rate():
    """Obtener win rate general"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        ROUND(100.0 * SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_rate_pct,
        COUNT(*) as total_trades,
        ROUND(SUM(pnl_usd), 2) as pnl_total,
        ROUND(AVG(pnl_usd), 2) as pnl_promedio
    FROM trades 
    WHERE closed_at IS NOT NULL
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_open_positions():
    """Obtener posiciones abiertas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        symbol,
        side,
        notional_usd,
        entry_price,
        created_at,
        ROUND((julianday('now') - julianday(created_at)) * 24, 1) as horas_abierta
    FROM trades 
    WHERE closed_at IS NULL
    ORDER BY created_at DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    return results

def main():
    """Función principal de monitoreo"""
    print("📊 MONITOREO EVENTARB BOT")
    print("=" * 50)
    
    # Verificar si la base de datos existe
    if not os.path.exists(os.getenv("DB_PATH", "trades.db")):
        print("❌ Base de datos no encontrada")
        return
    
    # 1. Resumen de trades por día
    print("\n📈 RESUMEN DIARIO (últimos 7 días):")
    print("-" * 40)
    trades_summary = get_trades_summary()
    if trades_summary:
        for fecha, total, notional, ganancias, perdidas in trades_summary:
            print(f"{fecha}: {total} trades, ${notional} notional, +${ganancias}/-${perdidas}")
    else:
        print("No hay trades registrados")
    
    # 2. PnL agregado
    print("\n💰 PnL AGREGADO (últimos 7 días):")
    print("-" * 40)
    pnl_summary = get_pnl_summary()
    if pnl_summary:
        for fecha, pnl_usd, pnl_pct, trades in pnl_summary:
            print(f"{fecha}: ${pnl_usd} ({pnl_pct}%), {trades} trades")
    else:
        print("No hay trades cerrados")
    
    # 3. Win Rate general
    print("\n🎯 MÉTRICAS GENERALES:")
    print("-" * 40)
    win_rate_data = get_win_rate()
    if win_rate_data and win_rate_data[1] > 0:
        win_rate, total, pnl_total, pnl_avg = win_rate_data
        print(f"Win Rate: {win_rate}%")
        print(f"Total Trades: {total}")
        print(f"PnL Total: ${pnl_total}")
        print(f"PnL Promedio: ${pnl_avg}")
    else:
        print("No hay suficientes datos para calcular métricas")
    
    # 4. Posiciones abiertas
    print("\n🔓 POSICIONES ABIERTAS:")
    print("-" * 40)
    open_positions = get_open_positions()
    if open_positions:
        for symbol, side, notional, entry_price, created_at, horas in open_positions:
            print(f"{symbol} {side}: ${notional} @ ${entry_price} ({horas}h)")
    else:
        print("No hay posiciones abiertas")
    
    print("\n" + "=" * 50)
    print("✅ Monitoreo completado")

if __name__ == "__main__":
    main()
