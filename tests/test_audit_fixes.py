#!/usr/bin/env python3
"""
Tests para las mejoras de auditoría del EventArb Bot
"""

import unittest
import sqlite3
import tempfile
import os
import sys
from decimal import Decimal
from datetime import datetime

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos del bot
from p1.daily_counter import (
    get_daily_count,
    calculate_daily_pnl,
    increment_daily_count,
    update_daily_loss,
    get_bot_state,
)


class TestAuditFixes(unittest.TestCase):
    """Test suite para las mejoras de auditoría"""

    def setUp(self):
        """Configurar base de datos temporal para tests"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Crear schema de prueba
        self.create_test_schema()

    def tearDown(self):
        """Limpiar después de los tests"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def create_test_schema(self):
        """Crear schema de prueba con las nuevas tablas"""
        conn = sqlite3.connect(self.db_path)

        # Crear tabla bot_state
        conn.execute(
            """
            CREATE TABLE bot_state (
                date TEXT PRIMARY KEY,
                trades_done INTEGER DEFAULT 0,
                loss_cents INTEGER DEFAULT 0,
                max_trades_per_day INTEGER DEFAULT 20,
                daily_loss_limit_cents INTEGER DEFAULT 10000,
                emergency_stop BOOLEAN DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Crear tabla event_fires con schema corregido
        conn.execute(
            """
            CREATE TABLE event_fires (
                event_id TEXT NOT NULL,
                window_sec INTEGER NOT NULL,
                fired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, window_sec)
            )
        """
        )

        # Crear tabla trades con schema corregido
        conn.execute(
            """
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity_cents INTEGER NOT NULL,
                entry_price_cents INTEGER NOT NULL,
                tp_price_cents INTEGER,
                sl_price_cents INTEGER,
                notional_usd_cents INTEGER NOT NULL,
                simulated BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def test_event_fires_idempotency(self):
        """Test que verifica la idempotencia de event_fires"""
        conn = sqlite3.connect(self.db_path)

        # Insertar evento con window_sec
        event_id = "test_event_123"
        window_sec = 300  # 5 minutos

        # Primera inserción
        conn.execute(
            """
            INSERT OR IGNORE INTO event_fires (event_id, window_sec, fired_at)
            VALUES (?, ?, ?)
        """,
            (event_id, window_sec, datetime.now().isoformat()),
        )

        # Segunda inserción con mismo window_sec (debería ser ignorada)
        conn.execute(
            """
            INSERT OR IGNORE INTO event_fires (event_id, window_sec, fired_at)
            VALUES (?, ?, ?)
        """,
            (event_id, window_sec, datetime.now().isoformat()),
        )

        conn.commit()

        # Verificar que solo hay una entrada
        cursor = conn.execute(
            "SELECT COUNT(*) FROM event_fires WHERE event_id = ?", (event_id,)
        )
        count = cursor.fetchone()[0]

        self.assertEqual(
            count, 1, "Debería haber solo una entrada por (event_id, window_sec)"
        )

        # Verificar que se puede insertar con diferente window_sec
        conn.execute(
            """
            INSERT OR IGNORE INTO event_fires (event_id, window_sec, fired_at)
            VALUES (?, ?, ?)
        """,
            (event_id, window_sec + 300, datetime.now().isoformat()),
        )

        conn.commit()

        cursor = conn.execute(
            "SELECT COUNT(*) FROM event_fires WHERE event_id = ?", (event_id,)
        )
        count = cursor.fetchone()[0]

        self.assertEqual(
            count, 2, "Debería permitir múltiples entradas con diferentes window_sec"
        )

        conn.close()

    def test_bot_state_persistence(self):
        """Test que verifica la persistencia del estado del bot"""
        # USAR UTC para consistencia con el bot
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # DEBUG: Verificar estado inicial
        state = get_bot_state(self.db_path)
        print(f"🔍 DEBUG: Estado inicial: {state}")
        print(f"🔍 DEBUG: Base de datos test: {self.db_path}")
        print(f"🔍 DEBUG: Fecha UTC buscada: {today}")
        self.assertEqual(state["trades_done"], 0)
        self.assertEqual(state["loss_cents"], 0)
        self.assertEqual(state["emergency_stop"], False)

        # DEBUG: Verificar que bot_state existe en la BD de test
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM bot_state WHERE date = ?", (today,))
        db_row = cursor.fetchone()
        print(f"🔍 DEBUG: Fila en BD test para {today}: {db_row}")

        # Si no hay fila, crearla
        if not db_row:
            print(f"🔍 DEBUG: Creando entrada para {today}")
            conn.execute(
                """
                INSERT INTO bot_state (date, trades_done, loss_cents, emergency_stop)
                VALUES (?, 0, 0, 0)
            """,
                (today,),
            )
            conn.commit()
            cursor = conn.execute("SELECT * FROM bot_state WHERE date = ?", (today,))
            db_row = cursor.fetchone()
            print(f"🔍 DEBUG: Fila creada: {db_row}")

        conn.close()

        # Incrementar contador de trades
        success = increment_daily_count(self.db_path)
        print(f"🔍 DEBUG: Incremento exitoso: {success}")
        self.assertTrue(success)

        # DEBUG: Verificar BD después del incremento
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM bot_state WHERE date = ?", (today,))
        db_row_after = cursor.fetchone()
        print(f"🔍 DEBUG: Fila en BD después: {db_row_after}")
        conn.close()

        # Verificar que se incrementó
        state = get_bot_state(self.db_path)
        print(f"🔍 DEBUG: Estado después: {state}")
        self.assertEqual(state["trades_done"], 1)

        # Actualizar pérdida
        success = update_daily_loss(5000, self.db_path)  # $50.00
        print(f"🔍 DEBUG: Update pérdida exitoso: {success}")
        self.assertTrue(success)

        # Verificar que se actualizó
        state = get_bot_state(self.db_path)
        print(f"🔍 DEBUG: Estado final: {state}")
        self.assertEqual(state["loss_cents"], 5000)

        # Verificar PnL como Decimal
        pnl = calculate_daily_pnl(self.db_path)
        print(f"🔍 DEBUG: PnL calculado: {pnl}")
        self.assertEqual(pnl, Decimal("50.00"))

    def test_daily_count_fallback(self):
        """Test que verifica el fallback a la tabla trades"""
        # Insertar trade en tabla trades
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO trades (event_id, symbol, side, quantity_cents, entry_price_cents, notional_usd_cents)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("test_event", "BTCUSDT", "BUY", 1000, 50000, 50000),
        )
        conn.commit()
        conn.close()

        # Verificar que get_daily_count funciona
        count_str = get_daily_count(self.db_path)
        self.assertIn("1", count_str)  # Debería mostrar 1 trade

    def test_emergency_stop_persistence(self):
        """Test que verifica la persistencia del emergency_stop"""
        conn = sqlite3.connect(self.db_path)
        # USAR UTC para consistencia con el bot
        today = datetime.utcnow().strftime("%Y-%m-%d")

        print(f"🔍 DEBUG: Fecha UTC para emergency_stop: {today}")

        # Activar emergency_stop
        conn.execute(
            """
            UPDATE bot_state SET emergency_stop = 1 WHERE date = ?
        """,
            (today,),
        )

        print(f"🔍 DEBUG: Filas actualizadas: {conn.total_changes}")

        # Si no hay fila, crear una
        if conn.total_changes == 0:
            print(f"🔍 DEBUG: Creando entrada para emergency_stop")
            conn.execute(
                """
                INSERT INTO bot_state (date, emergency_stop) VALUES (?, 1)
            """,
                (today,),
            )
            print(f"🔍 DEBUG: Fila creada")

        conn.commit()

        # DEBUG: Verificar BD
        cursor = conn.execute("SELECT * FROM bot_state WHERE date = ?", (today,))
        db_row = cursor.fetchone()
        print(f"🔍 DEBUG: Fila en BD: {db_row}")

        conn.close()

        # Verificar que se activó
        state = get_bot_state(self.db_path)
        print(f"🔍 DEBUG: Estado final: {state}")
        self.assertTrue(state["emergency_stop"])


if __name__ == "__main__":
    # Crear directorio de tests si no existe
    os.makedirs("tests", exist_ok=True)

    # Ejecutar tests
    unittest.main(verbosity=2)
