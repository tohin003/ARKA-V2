"""
core/pattern_learner.py — The Subconscious (Phase 6.1)

Analyzes ARKA's SQLite session history to discover behavioral patterns:
  - Most frequently used tools
  - Repeated request types
  - Time-of-day usage patterns

Discovered patterns are auto-appended to user_profile.md.
Runs as a Heartbeat job every 30 minutes.
"""

import sqlite3
import json
import os
from collections import Counter
from datetime import datetime
from typing import List, Dict
import structlog

logger = structlog.get_logger()

DB_PATH = os.path.expanduser("~/.arka/memory/session_history.db")


class PatternLearner:
    """Mines session history for behavioral patterns."""

    def __init__(self, db_path: str = DB_PATH, profile_path: str = "memory/user_profile.md"):
        self.db_path = db_path
        self.profile_path = profile_path

    def _query_recent_events(self, limit: int = 200) -> List[Dict]:
        """Fetch the last N events from the DB."""
        if not os.path.exists(self.db_path):
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error("pattern_learner_db_error", error=str(e))
            return []

    def _extract_tool_patterns(self, events: List[Dict]) -> List[str]:
        """Find most-used tools from tool_call events."""
        tool_mentions = []
        for e in events:
            if e.get("type") == "tool_call":
                tool_mentions.append(e.get("content", "unknown"))
            elif e.get("type") == "user_msg":
                content = e.get("content", "").lower()
                # Detect common request types
                if any(w in content for w in ["play", "music", "song"]):
                    tool_mentions.append("music_request")
                if any(w in content for w in ["send", "message", "whatsapp"]):
                    tool_mentions.append("messaging_request")
                if any(w in content for w in ["search", "find", "look up"]):
                    tool_mentions.append("search_request")
                if any(w in content for w in ["todo", "task", "remind"]):
                    tool_mentions.append("task_request")
                if any(w in content for w in ["remember", "my name", "my favorite"]):
                    tool_mentions.append("memory_request")

        counter = Counter(tool_mentions)
        patterns = []
        for item, count in counter.most_common(5):
            if count >= 2:  # Only surface patterns that appear at least twice
                patterns.append(f"User frequently uses: {item} ({count} times)")
        return patterns

    def _extract_time_patterns(self, events: List[Dict]) -> List[str]:
        """Detect time-of-day usage patterns."""
        hours = []
        for e in events:
            ts = e.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
                if dt:
                    hours.append(dt.hour)
            except (ValueError, TypeError):
                continue

        if not hours:
            return []

        counter = Counter(hours)
        patterns = []
        most_active = counter.most_common(1)
        if most_active:
            hour, count = most_active[0]
            if count >= 3:
                period = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 21 else "night"
                patterns.append(f"User is most active in the {period} (around {hour}:00)")
        return patterns

    def _already_known(self, pattern: str) -> bool:
        """Check if a pattern is already in the profile."""
        try:
            with open(self.profile_path, "r") as f:
                content = f.read()
            # Fuzzy match: check if the core of the pattern is already present
            # Extract the key phrase (after "User frequently uses: " or similar)
            key = pattern.split(": ", 1)[-1].split(" (")[0] if ": " in pattern else pattern
            return key.lower() in content.lower()
        except FileNotFoundError:
            return False

    def learn(self) -> List[str]:
        """
        Main entry point. Analyzes history and returns new patterns discovered.
        Auto-appends genuinely new patterns to user_profile.md.
        """
        events = self._query_recent_events()
        if not events:
            logger.info("pattern_learner_no_data")
            return []

        all_patterns = []
        all_patterns.extend(self._extract_tool_patterns(events))
        all_patterns.extend(self._extract_time_patterns(events))

        # Filter out already-known patterns
        new_patterns = [p for p in all_patterns if not self._already_known(p)]

        if new_patterns:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(self.profile_path, "a") as f:
                f.write(f"\n    - [{timestamp}] [Pattern] " + f"\n    - [{timestamp}] [Pattern] ".join(new_patterns))

            logger.info("pattern_learner_discovered", count=len(new_patterns), patterns=new_patterns)

        return new_patterns


# Singleton
pattern_learner = PatternLearner()
