#!/usr/bin/env python3
"""
Utilidades para la base de datos de EventArb Bot
"""

import datetime
import os
import sqlite3


def finalize_trade(db_path: str, trade_id: int, exit_price: float):
    """
    Finaliza un trade calculando PnL y marcando como cerrado

    Args:
        db_path: Ruta a la base de datos
        trade_id: ID del trade a cerrar
        exit_price: Precio de salida
    """
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Trae datos de la operación
        cur.execute(
            "SELECT side, entry_price, quantity FROM trades WHERE id=?", (trade_id,)
        )
        trade = cur.fetchone()

        if not trade:
            print(f"❌ Trade {trade_id} no encontrado")
            con.close()
            return False

        # Calcula PnL
        if trade["side"] == "BUY":
            pnl = (exit_price - trade["entry_price"]) * trade["quantity"]
        else:  # SELL
            pnl = (trade["entry_price"] - exit_price) * trade["quantity"]

        now = datetime.datetime.now().isoformat(timespec="seconds")

        # Actualiza el trade
        cur.execute(
            """
            UPDATE trades
            SET pnl_usd=?, closed_at=?
            WHERE id=?
        """,
            (pnl, now, trade_id),
        )

        con.commit()
        con.close()

        print(f"✅ Trade {trade_id} cerrado: PnL = ${pnl:.4f}")
        return True

    except Exception as e:
        print(f"❌ Error cerrando trade {trade_id}: {e}")
        return False


def get_trade_summary(db_path: str = None):
    """
    Obtiene resumen de trades para monitoreo

    Returns:
        dict con métricas clave
    """
    if db_path is None:
        db_path = os.getenv("DB_PATH", "trades.db")

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # Trades totales
        cur.execute("SELECT COUNT(*) FROM trades")
        total_trades = cur.fetchone()[0]

        # Trades cerrados hoy
        today = datetime.datetime.now().date().isoformat()
        cur.execute(
            "SELECT COUNT(*), COALESCE(SUM(pnl_usd), 0) FROM trades WHERE date(closed_at) = ?",
            (today,),
        )
        result = cur.fetchone()
        trades_today = result[0]
        pnl_today = result[1] or 0

        # Trades abiertos
        cur.execute("SELECT COUNT(*) FROM trades WHERE closed_at IS NULL")
        open_trades = cur.fetchone()[0]

        con.close()

        return {
            "total_trades": total_trades,
            "trades_today": trades_today,
            "pnl_today": pnl_today,
            "open_trades": open_trades,
        }

    except Exception as e:
        print(f"❌ Error obteniendo resumen: {e}")
        return {}


def close_all_simulated_trades(db_path: str = None):
    """
    Cierra todos los trades simulados (para testing)
    """
    if db_path is None:
        db_path = os.getenv("DB_PATH", "trades.db")

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()

        # Obtener trades simulados abiertos
        cur.execute(
            "SELECT id, side, entry_price, quantity, tp_price FROM trades WHERE simulated = 1 AND closed_at IS NULL"
        )
        trades = cur.fetchall()

        closed_count = 0
        for trade in trades:
            trade_id, side, entry_price, quantity, tp_price = trade

            if tp_price:
                # Usar tp_price como exit_price
                if side == "BUY":
                    pnl = (tp_price - entry_price) * quantity
                else:
                    pnl = (entry_price - tp_price) * quantity

                now = datetime.datetime.now().isoformat(timespec="seconds")

                cur.execute(
                    """
                    UPDATE trades
                    SET pnl_usd=?, closed_at=?
                    WHERE id=?
                """,
                    (pnl, now, trade_id),
                )

                closed_count += 1

        con.commit()
        con.close()

        print(f"✅ {closed_count} trades simulados cerrados")
        return closed_count

    except Exception as e:
        print(f"❌ Error cerrando trades simulados: {e}")
        return 0


if __name__ == "__main__":
    # Test de las funciones
    print("🧪 Test de utilidades de base de datos")

    # Resumen actual
    summary = get_trade_summary()
    print(f"📊 Resumen: {summary}")

    # Cerrar trades simulados si existen
    closed = close_all_simulated_trades()
    if closed > 0:
        print(f"🔄 Trades cerrados: {closed}")
        summary = get_trade_summary()
        print(f"📊 Resumen actualizado: {summary}")
