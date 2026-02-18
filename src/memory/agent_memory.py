import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List


class AgentMemory:
    """
    Persistent memory for the email agent.
    Stores preferences, feedback, and learning.
    Enhanced with sender context and triage corrections.
    """
    
    def __init__(self, db_path="agent_memory.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Create database schema."""
        
        # User preferences table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Feedback/corrections table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                email_from TEXT,
                email_subject TEXT,
                original_draft TEXT,
                edited_draft TEXT,
                feedback_note TEXT,
                action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Email history table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS email_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT UNIQUE,
                email_from TEXT,
                email_subject TEXT,
                triage_decision TEXT,
                action_taken TEXT,
                human_approved BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ✅ NEW: Sender context table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sender_context (
                sender_email TEXT PRIMARY KEY,
                sender_name TEXT,
                relationship TEXT,
                preferred_tone TEXT DEFAULT 'professional',
                notes TEXT,
                interaction_count INTEGER DEFAULT 0,
                triage_override TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ✅ NEW: Triage corrections table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS triage_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_from TEXT,
                email_subject TEXT,
                original_decision TEXT,
                corrected_decision TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Learning patterns table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_key TEXT,
                pattern_value TEXT,
                confidence REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_key)
            )
        """)
        
        self.conn.commit()
    
    # ===== PREFERENCES =====
    
    def set_preference(self, key: str, value: str):
        """Save a user preference."""
        self.conn.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now()))
        self.conn.commit()
    
    def get_preference(self, key: str, default=None) -> Optional[str]:
        """Get a user preference."""
        cursor = self.conn.execute(
            "SELECT value FROM preferences WHERE key = ?",
            (key,)
        )
        result = cursor.fetchone()
        return result[0] if result else default
    
    def get_all_preferences(self) -> Dict[str, str]:
        """Get all preferences as a dictionary."""
        cursor = self.conn.execute("SELECT key, value FROM preferences")
        return dict(cursor.fetchall())
    
    # ===== FEEDBACK =====
    
    def save_feedback(
        self,
        email_id: str,
        email_from: str,
        email_subject: str,
        original_draft: str,
        edited_draft: str,
        feedback_note: str = "",
        action: str = "edit"
    ):
        """Save human feedback/corrections."""
        self.conn.execute("""
            INSERT INTO feedback 
            (email_id, email_from, email_subject, original_draft, edited_draft, feedback_note, action)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (email_id, email_from, email_subject, original_draft, edited_draft, feedback_note, action))
        self.conn.commit()
        
        # Learn from the feedback
        self._learn_from_feedback(action, original_draft, edited_draft)
    
    def get_recent_feedback(self, email_from: str = None, limit: int = 10) -> List[Dict]:
        """Get recent feedback entries, optionally filtered by sender."""
        if email_from:
            cursor = self.conn.execute("""
                SELECT * FROM feedback 
                WHERE email_from = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (email_from, limit))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM feedback
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # ===== SENDER CONTEXT =====
    
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
        # Get existing context
        existing = self.get_sender_context(sender_email)
        
        if existing:
            # Update existing
            updates = []
            params = []
            
            if sender_name:
                updates.append("sender_name = ?")
                params.append(sender_name)
            if relationship:
                updates.append("relationship = ?")
                params.append(relationship)
            if preferred_tone:
                updates.append("preferred_tone = ?")
                params.append(preferred_tone)
            if notes:
                # Append to existing notes
                existing_notes = existing.get('notes', '')
                new_notes = f"{existing_notes}\n{notes}" if existing_notes else notes
                updates.append("notes = ?")
                params.append(new_notes)
            if triage_override:
                updates.append("triage_override = ?")
                params.append(triage_override)
            
            updates.append("interaction_count = interaction_count + 1")
            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(sender_email)
            
            if updates:
                query = f"UPDATE sender_context SET {', '.join(updates)} WHERE sender_email = ?"
                self.conn.execute(query, params)
        else:
            # Insert new
            self.conn.execute("""
                INSERT INTO sender_context 
                (sender_email, sender_name, relationship, preferred_tone, notes, triage_override, interaction_count)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (sender_email, sender_name, relationship, preferred_tone or 'professional', notes, triage_override))
        
        self.conn.commit()
    
    def get_sender_context(self, sender_email: str) -> Optional[Dict]:
        """Get sender context."""
        cursor = self.conn.execute("""
            SELECT * FROM sender_context
            WHERE sender_email = ?
        """, (sender_email,))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        return None
    
    # ===== TRIAGE CORRECTIONS =====
    
    def save_triage_correction(
        self,
        email_from: str,
        email_subject: str,
        original_decision: str,
        corrected_decision: str,
        reason: str = ""
    ):
        """Save a triage correction for learning."""
        self.conn.execute("""
            INSERT INTO triage_corrections 
            (email_from, email_subject, original_decision, corrected_decision, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (email_from, email_subject, original_decision, corrected_decision, reason))
        self.conn.commit()
    
    def get_triage_corrections(self, email_from: str = None, limit: int = 10) -> List[Dict]:
        """Get recent triage corrections."""
        if email_from:
            cursor = self.conn.execute("""
                SELECT * FROM triage_corrections
                WHERE email_from = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (email_from, limit))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM triage_corrections
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # ===== FULL CONTEXT =====
    
    def get_full_context(self, sender_email: str = None) -> Dict:
        """
        Get complete context for memory-informed decisions.
        This is what load_memory_node calls.
        """
        context = {
            "preferences": self.get_all_preferences(),
            "sender_context": None,
            "past_feedback": [],
            "triage_corrections": []
        }
        
        if sender_email:
            # Get sender-specific data
            context["sender_context"] = self.get_sender_context(sender_email)
            context["past_feedback"] = self.get_recent_feedback(email_from=sender_email, limit=5)
            context["triage_corrections"] = self.get_triage_corrections(email_from=sender_email, limit=5)
        
        return context
    
    # ===== LEARNING =====
    
    def _learn_from_feedback(self, action_type: str, original: str, edited: str):
        """Analyze feedback and extract learning patterns."""
        # 1. Tone preferences
        if len(edited) < len(original):
            self._increment_pattern("tone_preference", "concise", 0.8)
        
        # 2. Common phrases to avoid/use
        original_words = set(original.lower().split())
        edited_words = set(edited.lower().split())
        
        removed_words = original_words - edited_words
        added_words = edited_words - original_words
        
        for word in removed_words:
            if len(word) > 3:  # Skip small words
                self._increment_pattern("avoid_words", word, 0.5)
        
        for word in added_words:
            if len(word) > 3:
                self._increment_pattern("prefer_words", word, 0.5)
    
    def _increment_pattern(self, pattern_type: str, pattern_key: str, confidence: float):
        """Increment usage count for a learned pattern."""
        self.conn.execute("""
            INSERT INTO learned_patterns (pattern_type, pattern_key, pattern_value, confidence, usage_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                usage_count = usage_count + 1,
                confidence = MIN(1.0, confidence + 0.1)
        """, (pattern_type, pattern_key, json.dumps({"count": 1}), confidence))
        self.conn.commit()
    
    def get_learned_patterns(self, pattern_type: str = None) -> List[Dict]:
        """Get learned patterns, optionally filtered by type."""
        if pattern_type:
            cursor = self.conn.execute("""
                SELECT * FROM learned_patterns
                WHERE pattern_type = ?
                ORDER BY confidence DESC, usage_count DESC
            """, (pattern_type,))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM learned_patterns
                ORDER BY confidence DESC, usage_count DESC
            """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # ===== EMAIL HISTORY =====
    
    def save_email_interaction(
        self,
        email_id: str,
        email_from: str,
        email_subject: str,
        triage_decision: str,
        action_taken: str,
        human_approved: bool
    ):
        """Save email interaction to history."""
        self.conn.execute("""
            INSERT OR REPLACE INTO email_history 
            (email_id, email_from, email_subject, triage_decision, action_taken, human_approved)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (email_id, email_from, email_subject, triage_decision, action_taken, human_approved))
        self.conn.commit()
    
    def get_sender_history(self, email_from: str, limit: int = 5) -> List[Dict]:
        """Get past interactions with a specific sender."""
        cursor = self.conn.execute("""
            SELECT * FROM email_history
            WHERE email_from = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (email_from, limit))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # ===== INSIGHTS =====
    
    def get_approval_rate(self) -> float:
        """Calculate % of actions approved by human."""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(CASE WHEN human_approved = 1 THEN 1 END) * 100.0 / COUNT(*) as approval_rate
            FROM email_history
            WHERE action_taken != 'none'
        """)
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        stats = {}
        
        # Total emails processed
        cursor = self.conn.execute("SELECT COUNT(*) FROM email_history")
        stats["total_emails"] = cursor.fetchone()[0]
        
        # Approval rate
        stats["approval_rate"] = self.get_approval_rate()
        
        # Learned patterns count
        cursor = self.conn.execute("SELECT COUNT(*) FROM learned_patterns")
        stats["learned_patterns"] = cursor.fetchone()[0]
        
        # Preferences count
        cursor = self.conn.execute("SELECT COUNT(*) FROM preferences")
        stats["preferences"] = cursor.fetchone()[0]
        
        # Sender contexts count
        cursor = self.conn.execute("SELECT COUNT(*) FROM sender_context")
        stats["known_senders"] = cursor.fetchone()[0]
        
        # Triage corrections count
        cursor = self.conn.execute("SELECT COUNT(*) FROM triage_corrections")
        stats["triage_corrections"] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection."""
        self.conn.close()