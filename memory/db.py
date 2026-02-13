import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from memory.config import AUTO_UPDATE_ENV, AUTO_UPDATE_DEFAULT
from memory.distiller import distill_user_text
from memory.store import memory_store

logger = structlog.get_logger()

DB_PATH = os.path.expanduser("~/.arka/memory/session_history.db")

class MemoryClient:
    """
    Handles persistent storage for ARKA sessions using SQLite.
    Stores:
    - Session ID
    - User Messages
    - Agent Thoughts/Plans
    - Tool Executions & Results
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """Create table if not exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Events Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type TEXT,  -- 'user_msg', 'agent_thought', 'tool_call', 'tool_result'
                    content TEXT,
                    metadata TEXT -- JSON string
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("db_init_failed", error=str(e))

    def log_event(self, session_id: str, type: str, content: str, metadata: Dict[str, Any] = None):
        """Log an event to the DB."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            meta_json = json.dumps(metadata) if metadata else "{}"
            
            cursor.execute('''
                INSERT INTO events (session_id, type, content, metadata)
                VALUES (?, ?, ?, ?)
            ''', (session_id, type, content, meta_json))
            
            conn.commit()
            conn.close()

            # Also write to unified MemoryStore (best-effort)
            event_id = memory_store.add_event(session_id, type, content, metadata)
            if event_id and type == "user_msg":
                if os.getenv(AUTO_UPDATE_ENV, AUTO_UPDATE_DEFAULT) == "1":
                    try:
                        distill_user_text(memory_store, event_id, content)
                    except Exception as e:
                        logger.warning("memory_auto_distill_failed", error=str(e))
        except Exception as e:
            logger.error("db_log_failed", error=str(e))

    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve recent history for a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM events 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                events.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "type": row["type"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"])
                })
            return events[::-1] # Return chronological order
        except Exception as e:
            logger.error("db_read_failed", error=str(e))
            return []

# Singleton
memory_client = MemoryClient()
