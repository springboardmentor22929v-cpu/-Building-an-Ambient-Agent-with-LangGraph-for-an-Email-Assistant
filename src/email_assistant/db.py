import sqlite3
from pathlib import Path

# 🔥 Permanent DB path (project root/.db/memory.db)
DB_PATH = Path(__file__).resolve().parents[2] / ".db" / "memory.db"


def get_connection():
    """Create SQLite connection."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database and tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            namespace TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY(namespace, key)
        )
    """)

    conn.commit()
    conn.close()


# initialize automatically when imported
init_db()
