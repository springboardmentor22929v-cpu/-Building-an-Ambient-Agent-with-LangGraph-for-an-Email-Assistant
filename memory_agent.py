"""
AgentMemory - SQLite-based persistent memory for Email Assistant
Milestone 4: Persistent Memory & Learning
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class AgentMemory:
    """
    SQLite-based memory system for the email agent.
    Stores user preferences, sender context, and feedback for learning.
    """
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for sender context (who emails are from)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sender_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email TEXT UNIQUE NOT NULL,
                sender_name TEXT,
                relationship TEXT,
                preferred_tone TEXT DEFAULT 'professional',
                notes TEXT,
                triage_override TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for email interactions history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                sender_email TEXT NOT NULL,
                subject TEXT,
                triage_decision TEXT,
                action_taken TEXT,
                human_approved INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for human feedback (edits)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                sender_email TEXT NOT NULL,
                subject TEXT,
                original_draft TEXT,
                edited_draft TEXT,
                feedback_note TEXT,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for triage corrections
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS triage_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email TEXT NOT NULL,
                subject TEXT,
                original_decision TEXT,
                corrected_decision TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table for general user preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    # ==========================
    # Sender Context Methods
    # ==========================
    
    def save_sender_context(
        self,
        sender_email: str,
        sender_name: str = None,
        relationship: str = None,
        preferred_tone: str = None,
        notes: str = None,
        triage_override: str = None
    ):
        """Save or update sender context."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if sender exists
        cursor.execute(
            "SELECT id FROM sender_context WHERE sender_email = ?",
            (sender_email,)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update
            updates = []
            params = []
            if sender_name is not None:
                updates.append("sender_name = ?")
                params.append(sender_name)
            if relationship is not None:
                updates.append("relationship = ?")
                params.append(relationship)
            if preferred_tone is not None:
                updates.append("preferred_tone = ?")
                params.append(preferred_tone)
            if notes is not None:
                # Append to existing notes
                cursor.execute("SELECT notes FROM sender_context WHERE sender_email = ?", (sender_email,))
                existing = cursor.fetchone()
                existing_notes = existing[0] if existing and existing[0] else ""
                new_notes = existing_notes + "\n" + notes if existing_notes else notes
                updates.append("notes = ?")
                params.append(new_notes)
            if triage_override is not None:
                updates.append("triage_override = ?")
                params.append(triage_override)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(sender_email)
            
            if updates:
                cursor.execute(
                    f"UPDATE sender_context SET {', '.join(updates)} WHERE sender_email = ?",
                    params
                )
        else:
            # Insert
            cursor.execute("""
                INSERT INTO sender_context 
                (sender_email, sender_name, relationship, preferred_tone, notes, triage_override)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sender_email, sender_name, relationship, preferred_tone, notes, triage_override))
        
        conn.commit()
        conn.close()
    
    def get_sender_context(self, sender_email: str) -> Optional[Dict]:
        """Get sender context."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM sender_context WHERE sender_email = ?",
            (sender_email,)
        )
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    # ==========================
    # Email Interaction Methods
    # ==========================
    
    def save_email_interaction(
        self,
        email_id: str,
        sender_email: str,
        email_subject: str,
        triage_decision: str,
        action_taken: str,
        human_approved: bool = False
    ):
        """Save an email interaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO email_interactions 
            (email_id, sender_email, subject, triage_decision, action_taken, human_approved)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email_id, sender_email, email_subject, triage_decision, action_taken, 1 if human_approved else 0))
        
        conn.commit()
        conn.close()
    
    def get_interaction_count(self, sender_email: str) -> int:
        """Get total interaction count for a sender."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM email_interactions WHERE sender_email = ?",
            (sender_email,)
        )
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    # ==========================
    # Feedback Methods
    # ==========================
    
    def save_feedback(
        self,
        email_id: str,
        sender_email: str,
        email_subject: str,
        original_draft: str,
        edited_draft: str,
        feedback_note: str = "",
        action: str = "edit"
    ):
        """Save human feedback (edits)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback 
            (email_id, sender_email, subject, original_draft, edited_draft, feedback_note, action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email_id, sender_email, email_subject, original_draft, edited_draft, feedback_note, action))
        
        conn.commit()
        conn.close()
    
    def get_past_feedback(self, sender_email: str, limit: int = 10) -> List[Dict]:
        """Get past feedback for a sender."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM feedback 
            WHERE sender_email = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (sender_email, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==========================
    # Triage Correction Methods
    # ==========================
    
    def save_triage_correction(
        self,
        email_from: str,
        email_subject: str,
        original_decision: str,
        corrected_decision: str,
        reason: str = ""
    ):
        """Save a triage correction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO triage_corrections 
            (sender_email, subject, original_decision, corrected_decision, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (email_from, email_subject, original_decision, corrected_decision, reason))
        
        conn.commit()
        conn.close()
    
    def get_triage_corrections(self, email_from: str) -> List[Dict]:
        """Get triage corrections for a sender."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM triage_corrections 
            WHERE sender_email = ?
            ORDER BY timestamp DESC
        """, (email_from,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==========================
    # User Preferences Methods
    # ==========================
    
    def save_preference(self, key: str, value: str):
        """Save a user preference."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
        conn.close()
    
    def get_preferences(self) -> Dict:
        """Get all user preferences."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_preferences")
        rows = cursor.fetchall()
        
        conn.close()
        
        return {row["key"]: row["value"] for row in rows}
    
    # ==========================
    # Full Context Method
    # ==========================
    
    def get_full_context(self, sender_email: str) -> Dict:
        """Get full context for a sender including preferences, feedback, etc."""
        return {
            "sender_context": self.get_sender_context(sender_email),
            "past_feedback": self.get_past_feedback(sender_email),
            "triage_corrections": self.get_triage_corrections(sender_email),
            "preferences": self.get_preferences(),
            "interaction_count": self.get_interaction_count(sender_email)
        }


# Test function
if __name__ == "__main__":
    # Test the memory
    memory = AgentMemory("test_memory.db")
    
    # Test saving sender context
    memory.save_sender_context(
        sender_email="bob@company.com",
        sender_name="Robert",
        notes="Prefers to be called Robert"
    )
    
    # Test getting context
    ctx = memory.get_sender_context("bob@company.com")
    print("Sender context:", ctx)
    
    # Test full context
    full = memory.get_full_context("bob@company.com")
    print("Full context:", full)
    
    print("✅ AgentMemory working!")
