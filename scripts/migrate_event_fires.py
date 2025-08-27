#!/usr/bin/env python3
"""
Migration script for EventArb Bot - Event Fires Idempotency Fix

This script migrates the event_fires table from the old schema:
- OLD: PRIMARY KEY(event_id, fired_at)
- NEW: PRIMARY KEY(event_id, window_sec)

The window_sec represents a time window (e.g., 300 seconds = 5 minutes)
to ensure idempotency of event firing.
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta


def connect_db():
    """Connect to the trades database"""
    db_path = "trades.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    return sqlite3.connect(db_path)


def backup_table(conn, table_name):
    """Create a backup of the existing table"""
    backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        conn.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM {table_name}")
        print(f"✅ Backup created: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None


def migrate_event_fires(conn):
    """Migrate event_fires table to new schema"""
    print("🔄 Starting event_fires migration...")

    # Check if old table exists
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='event_fires'"
    )
    if not cursor.fetchone():
        print("ℹ️  event_fires table doesn't exist, creating new one...")
        create_new_event_fires(conn)
        return True

    # Check current schema
    cursor = conn.execute("PRAGMA table_info(event_fires)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    if "window_sec" in columns:
        print("✅ event_fires table already migrated")
        return True

    print("📋 Current schema detected:")
    for col_name, col_type in columns.items():
        print(f"   - {col_name}: {col_type}")

    # Create backup
    backup_name = backup_table(conn, "event_fires")
    if not backup_name:
        return False

    try:
        # Create new table with correct schema
        create_new_event_fires(conn)

        # Migrate data if exists
        migrate_data(conn, backup_name)

        # Drop old table
        conn.execute("DROP TABLE event_fires")

        # Rename new table
        conn.execute("ALTER TABLE event_fires_new RENAME TO event_fires")

        print("✅ Migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"🔄 Restoring from backup: {backup_name}")

        # Restore from backup
        conn.execute("DROP TABLE IF EXISTS event_fires")
        conn.execute(f"ALTER TABLE {backup_name} RENAME TO event_fires")
        return False


def create_new_event_fires(conn):
    """Create new event_fires table with correct schema"""
    conn.execute(
        """
        CREATE TABLE event_fires_new (
            event_id TEXT NOT NULL,
            window_sec INTEGER NOT NULL,
            fired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id, window_sec)
        )
    """
    )
    print("✅ New event_fires table created")


def migrate_data(conn, backup_name):
    """Migrate data from old table to new table"""
    try:
        # Get data from backup
        cursor = conn.execute(f"SELECT event_id, fired_at FROM {backup_name}")
        rows = cursor.fetchall()

        if not rows:
            print("ℹ️  No data to migrate")
            return

        print(f"📊 Migrating {len(rows)} records...")

        # Convert fired_at to window_sec (5-minute windows)
        migrated_count = 0
        for event_id, fired_at in rows:
            try:
                # Parse fired_at and convert to window_sec
                if fired_at:
                    dt = datetime.fromisoformat(fired_at.replace("Z", "+00:00"))
                    # Convert to 5-minute window (300 seconds)
                    window_sec = (dt.hour * 3600 + dt.minute * 60) // 300 * 300
                else:
                    window_sec = 0

                conn.execute(
                    """
                    INSERT OR IGNORE INTO event_fires_new (event_id, window_sec, fired_at)
                    VALUES (?, ?, ?)
                """,
                    (event_id, window_sec, fired_at),
                )

                migrated_count += 1

            except Exception as e:
                print(f"⚠️  Warning: Could not migrate record {event_id}: {e}")

        print(f"✅ Migrated {migrated_count} records")

    except Exception as e:
        print(f"❌ Error during data migration: {e}")
        raise


def create_bot_state_table(conn):
    """Create bot_state table if it doesn't exist"""
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_state (
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
        print("✅ bot_state table created/verified")

        # Initialize today's state if not exists
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            """
            INSERT OR IGNORE INTO bot_state (date, trades_done, loss_cents, emergency_stop)
            VALUES (?, 0, 0, 0)
        """,
            (today,),
        )

    except Exception as e:
        print(f"❌ Error creating bot_state table: {e}")


def main():
    """Main migration function"""
    print("🚀 EventArb Bot - Event Fires Migration Script")
    print("=" * 50)

    try:
        conn = connect_db()

        # Migrate event_fires table
        if migrate_event_fires(conn):
            # Create bot_state table
            create_bot_state_table(conn)

            # Commit changes
            conn.commit()
            print("✅ All migrations completed successfully!")

        else:
            print("❌ Migration failed, rolling back...")
            conn.rollback()
            sys.exit(1)

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
