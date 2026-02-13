import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

from memory.config import (
    DEFAULT_MEMORY_DB_PATH,
    DEFAULT_FACT_TTL_DAYS,
    DEFAULT_EVENT_TTL_DAYS,
    DEFAULT_EPISODE_TTL_DAYS,
)

logger = structlog.get_logger()


class MemoryStore:
    """
    Unified persistent memory store.

    Tables:
      - events: raw session events
      - facts: distilled, long-term semantic facts
    """

    def __init__(self, db_path: str = DEFAULT_MEMORY_DB_PATH):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._ensure_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    type TEXT,
                    content TEXT,
                    metadata TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    confidence REAL DEFAULT 0.7,
                    source_event_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME,
                    expires_at DATETIME,
                    locked INTEGER DEFAULT 0,
                    is_deleted INTEGER DEFAULT 0,
                    deleted_at DATETIME,
                    metadata TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    summary TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    metadata TEXT
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_facts_sp ON facts(subject, predicate)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_facts_deleted ON facts(is_deleted)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id)"
            )
            # Ensure new columns exist for older DBs
            self._ensure_columns(conn, "facts", {"locked": "INTEGER DEFAULT 0"})
            conn.commit()

    def _ensure_columns(self, conn: sqlite3.Connection, table: str, columns: Dict[str, str]) -> None:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}
        for col, ddl in columns.items():
            if col in existing:
                continue
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")

    def add_event(
        self,
        session_id: str,
        event_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        meta_json = json.dumps(metadata or {})
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO events (session_id, type, content, metadata)
                        VALUES (?, ?, ?, ?)
                        """,
                        (session_id, event_type, content, meta_json),
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error("memory_add_event_failed", error=str(e))
                return None

    def upsert_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.7,
        source_event_id: Optional[int] = None,
        ttl_days: Optional[int] = DEFAULT_FACT_TTL_DAYS,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        subject = subject.strip()
        predicate = predicate.strip()
        obj = obj.strip()
        if not subject or not predicate or not obj:
            return None

        expires_at = None
        if ttl_days is not None:
            expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()

        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT id, object, metadata, confidence
                        FROM facts
                        WHERE subject = ? AND predicate = ? AND is_deleted = 0
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT 1
                        """,
                        (subject, predicate),
                    )
                    row = cursor.fetchone()

                    if row:
                        existing_meta = {}
                        try:
                            existing_meta = json.loads(row["metadata"]) if row["metadata"] else {}
                        except Exception:
                            existing_meta = {}

                        history = existing_meta.get("history", [])
                        if row["object"] != obj:
                            history.append(
                                {
                                    "object": row["object"],
                                    "confidence": row["confidence"],
                                    "updated_at": datetime.now().isoformat(),
                                }
                            )

                        merged_meta = (metadata or {}).copy()
                        if history:
                            merged_meta["history"] = history

                        cursor.execute(
                            """
                            UPDATE facts
                            SET object = ?,
                                confidence = ?,
                                source_event_id = ?,
                                updated_at = ?,
                                expires_at = ?,
                                metadata = ?
                            WHERE id = ?
                            """,
                            (
                                obj,
                                confidence,
                                source_event_id,
                                datetime.now().isoformat(),
                                expires_at,
                                json.dumps(merged_meta),
                                row["id"],
                            ),
                        )
                        conn.commit()
                        return int(row["id"])

                    meta_json = json.dumps(metadata or {})
                    cursor.execute(
                        """
                        INSERT INTO facts (
                            subject, predicate, object, confidence,
                            source_event_id, expires_at, metadata
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            subject,
                            predicate,
                            obj,
                            confidence,
                            source_event_id,
                            expires_at,
                            meta_json,
                        ),
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error("memory_upsert_fact_failed", error=str(e))
                return None

    def insert_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.6,
        source_event_id: Optional[int] = None,
        ttl_days: Optional[int] = DEFAULT_FACT_TTL_DAYS,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        subject = subject.strip()
        predicate = predicate.strip()
        obj = obj.strip()
        if not subject or not predicate or not obj:
            return None

        expires_at = None
        if ttl_days is not None:
            expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()

        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    meta_json = json.dumps(metadata or {})
                    cursor.execute(
                        """
                        INSERT INTO facts (
                            subject, predicate, object, confidence,
                            source_event_id, expires_at, metadata
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            subject,
                            predicate,
                            obj,
                            confidence,
                            source_event_id,
                            expires_at,
                            meta_json,
                        ),
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error("memory_insert_fact_failed", error=str(e))
                return None

    def search_facts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not query:
            return []
        like = f"%{query.strip()}%"
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT * FROM facts
                        WHERE is_deleted = 0
                          AND (subject LIKE ? OR predicate LIKE ? OR object LIKE ?)
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT ?
                        """,
                        (like, like, like, limit),
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_dict(row) for row in rows]
            except Exception as e:
                logger.error("memory_search_facts_failed", error=str(e))
                return []

    def get_fact_by_id(self, fact_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    if include_deleted:
                        cursor.execute("SELECT * FROM facts WHERE id = ?", (fact_id,))
                    else:
                        cursor.execute("SELECT * FROM facts WHERE id = ? AND is_deleted = 0", (fact_id,))
                    row = cursor.fetchone()
                    return self._row_to_dict(row) if row else None
            except Exception as e:
                logger.error("memory_get_fact_failed", error=str(e))
                return None

    def get_recent_facts(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT * FROM facts
                        WHERE is_deleted = 0
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT ?
                        """,
                        (limit,),
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_dict(row) for row in rows]
            except Exception as e:
                logger.error("memory_get_recent_facts_failed", error=str(e))
                return []

    def mark_fact_deleted(self, fact_id: int, reason: str = "") -> bool:
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT metadata FROM facts WHERE id = ?", (fact_id,))
                    row = cursor.fetchone()
                    meta = {}
                    if row and row["metadata"]:
                        try:
                            meta = json.loads(row["metadata"])
                        except Exception:
                            meta = {}
                    if reason:
                        meta["delete_reason"] = reason
                    cursor.execute(
                        """
                        UPDATE facts
                        SET is_deleted = 1,
                            deleted_at = ?,
                            metadata = ?
                        WHERE id = ?
                        """,
                        (datetime.now().isoformat(), json.dumps(meta), fact_id),
                    )
                    conn.commit()
                    return True
            except Exception as e:
                logger.error("memory_mark_fact_deleted_failed", error=str(e))
                return False

    def cleanup_expired_facts(self) -> int:
        """Mark expired facts as deleted. Returns count."""
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE facts
                        SET is_deleted = 1,
                            deleted_at = ?
                        WHERE is_deleted = 0
                          AND locked = 0
                          AND expires_at IS NOT NULL
                          AND expires_at <= ?
                        """,
                        (datetime.now().isoformat(), datetime.now().isoformat()),
                    )
                    conn.commit()
                    return cursor.rowcount or 0
            except Exception as e:
                logger.error("memory_cleanup_expired_failed", error=str(e))
                return 0

    def purge_facts_older_than(self, days: int) -> int:
        """Mark facts older than N days as deleted. Returns count."""
        if days <= 0:
            return 0
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        UPDATE facts
                        SET is_deleted = 1,
                            deleted_at = ?
                        WHERE is_deleted = 0
                          AND locked = 0
                          AND datetime(COALESCE(updated_at, created_at)) <= datetime(?)
                        """,
                        (datetime.now().isoformat(), cutoff_str),
                    )
                    conn.commit()
                    return cursor.rowcount or 0
            except Exception as e:
                logger.error("memory_purge_facts_failed", error=str(e))
                return 0

    def add_episode(
        self,
        session_id: str,
        summary: str,
        ttl_days: Optional[int] = DEFAULT_EPISODE_TTL_DAYS,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        if not summary:
            return None
        expires_at = None
        if ttl_days is not None:
            expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO episodes (session_id, summary, expires_at, metadata)
                        VALUES (?, ?, ?, ?)
                        """,
                        (session_id, summary.strip(), expires_at, json.dumps(metadata or {})),
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error("memory_add_episode_failed", error=str(e))
                return None

    def get_recent_episodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT * FROM episodes
                        ORDER BY created_at DESC
                        LIMIT ?
                        """,
                        (limit,),
                    )
                    rows = cursor.fetchall()
                    return [self._row_to_dict(row) for row in rows]
            except Exception as e:
                logger.error("memory_get_recent_episodes_failed", error=str(e))
                return []

    def cleanup_events(self, ttl_days: int = DEFAULT_EVENT_TTL_DAYS) -> int:
        if not ttl_days:
            return 0
        cutoff = datetime.now() - timedelta(days=ttl_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM events WHERE timestamp < ?",
                        (cutoff_str,),
                    )
                    conn.commit()
                    return cursor.rowcount or 0
            except Exception as e:
                logger.error("memory_cleanup_events_failed", error=str(e))
                return 0

    def cleanup_episodes(self, ttl_days: int = DEFAULT_EPISODE_TTL_DAYS) -> int:
        if not ttl_days:
            return 0
        cutoff = datetime.now() - timedelta(days=ttl_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM episodes WHERE created_at < ?",
                        (cutoff_str,),
                    )
                    conn.commit()
                    return cursor.rowcount or 0
            except Exception as e:
                logger.error("memory_cleanup_episodes_failed", error=str(e))
                return 0

    def mark_fact_locked(self, fact_id: int, locked: bool = True) -> bool:
        with self._lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE facts SET locked = ? WHERE id = ?",
                        (1 if locked else 0, fact_id),
                    )
                    conn.commit()
                    return True
            except Exception as e:
                logger.error("memory_mark_fact_locked_failed", error=str(e))
                return False

    def export_facts(self, path: str, include_deleted: bool = False) -> str:
        with self._lock:
            with self._connect() as conn:
                cursor = conn.cursor()
                if include_deleted:
                    cursor.execute("SELECT * FROM facts")
                else:
                    cursor.execute("SELECT * FROM facts WHERE is_deleted = 0")
                rows = cursor.fetchall()
                data = [self._row_to_dict(row) for row in rows]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM facts WHERE is_deleted = 0")
                facts = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM events")
                events = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM episodes")
                episodes = cursor.fetchone()[0]
        return {"facts": facts, "events": events, "episodes": episodes}

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        if "metadata" in data and data["metadata"]:
            try:
                data["metadata"] = json.loads(data["metadata"])
            except Exception:
                pass
        return data


# Singleton
memory_store = MemoryStore()
