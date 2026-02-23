import sqlite3
import json
from typing import List, Dict, Any

DB_PATH = "agent_memory.sqlite"

def init_memory():
    """Initialize the SQLite database for persistent memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for user preferences/facts learned over time
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            confidence FLOAT DEFAULT 1.0,
            source TEXT
        )
    ''')
    
    # Table for logging learning events (audit trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_draft TEXT,
            corrected_draft TEXT,
            learned_preference TEXT
        )
    ''')

    # Table for logging processed emails (interaction history)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            sender TEXT,
            subject TEXT,
            body_preview TEXT,
            decision TEXT,
            generated_draft TEXT,
            status TEXT,
            workflow_steps TEXT
        )
    ''')

    # Add workflow_steps column if it doesn't exist (for existing DBs)
    try:
        cursor.execute('ALTER TABLE processed_emails ADD COLUMN workflow_steps TEXT')
    except:
        pass  # Column already exists

    conn.commit()
    conn.close()
    print("🧠 Persistent memory initialized (SQLite).")

def store_preference(key: str, value: str, source: str = "hitl_correction"):
    """Store or update a user preference."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO user_preferences (key, value, source)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            source = excluded.source
        ''', (key, value, source))
        conn.commit()
        print(f"🧠 MEMORY UPDATED: {key} = {value}")
    except Exception as e:
        print(f"❌ Error updating memory: {e}")
    finally:
        conn.close()

def get_all_preferences() -> Dict[str, str]:
    """Retrieve all stored user preferences as a dictionary."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT key, value FROM user_preferences')
    rows = cursor.fetchall()
    
    conn.close()
    
    return {row[0]: row[1] for row in rows}

def log_learning_event(original: str, corrected: str, preference: str):
    """Log a learning event for evaluation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO learning_history (original_draft, corrected_draft, learned_preference)
        VALUES (?, ?, ?)
    ''', (original, corrected, preference))
    
    conn.commit()
    conn.close()

def log_processed_email(sender: str, subject: str, body: str, decision: str, generated_draft: str = None, status: str = "processed", workflow_steps: str = None):
    """Log the outcome of processing an email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO processed_emails (sender, subject, body_preview, decision, generated_draft, status, workflow_steps)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (sender, subject, body[:200] if body else '', decision, generated_draft, status, workflow_steps))
    
    conn.commit()
    conn.close()
    print(f"📄 Logged email processing: {status}")

def get_email_history(sender: str = None) -> List[Dict[str, Any]]:
    """Retrieve processing history, optionally filtered by sender."""
    import json as _json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if sender:
        cursor.execute('''
            SELECT id, timestamp, sender, subject, body_preview, decision, status, generated_draft, workflow_steps 
            FROM processed_emails 
            WHERE sender = ? 
            ORDER BY timestamp DESC LIMIT 20
        ''', (sender,))
    else:
        cursor.execute('''
            SELECT id, timestamp, sender, subject, body_preview, decision, status, generated_draft, workflow_steps 
            FROM processed_emails 
            ORDER BY timestamp DESC LIMIT 20
        ''')
        
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        steps = None
        if r[8]:
            try:
                steps = _json.loads(r[8])
            except:
                steps = None
        results.append({
            "id": r[0],
            "timestamp": r[1],
            "sender": r[2],
            "subject": r[3],
            "body_preview": r[4],
            "decision": r[5],
            "status": r[6],
            "generated_draft": r[7],
            "workflow_steps": steps
        })
    return results


def delete_processed_email(email_id: int) -> bool:
    """Delete a specific processed email entry by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM processed_emails WHERE id = ?', (email_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Initialize on module load check
if __name__ == "__main__":
    init_memory()
