
import sqlite3

DB_NAME = "cookmate.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            quantity TEXT DEFAULT '1',
            expiry_date TEXT,
            notified INTEGER DEFAULT 0
        )
    """)

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(ingredients)"
        ).fetchall()
    ]

    if "last_reminded_days" not in columns:
        conn.execute("""
            ALTER TABLE ingredients
            ADD COLUMN last_reminded_days INTEGER
        """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialize_database()
    print("CookMate AI database is ready!")
