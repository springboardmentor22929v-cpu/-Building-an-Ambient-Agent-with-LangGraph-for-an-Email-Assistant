import sqlite3
from typing import Optional

DB_PATH = 'data/agent_memory.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)'
    )
    cur.execute(
        'CREATE TABLE IF NOT EXISTS interactions (id INTEGER PRIMARY KEY AUTOINCREMENT, email_id TEXT, classification TEXT, feedback TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'
    )
    conn.commit()
    conn.close()


def set_kv(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('REPLACE INTO kv (key,value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()


def get_kv(key: str) -> Optional[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT value FROM kv WHERE key = ?', (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def log_interaction(email_id: str, classification: str, feedback: str = None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO interactions (email_id, classification, feedback) VALUES (?, ?, ?)', (email_id, classification, feedback))
    conn.commit()
    conn.close()
