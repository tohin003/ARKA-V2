"""
core/reflection.py — Reflection Loop (Phase 6.3)

After each session, analyzes what happened and extracts learnings.
Learnings are saved to memory/learnings.md and injected into the
system prompt on next boot.
"""

import os
from datetime import datetime
from typing import List
import structlog

logger = structlog.get_logger()

LEARNINGS_FILE = "memory/learnings.md"
MAX_LEARNINGS = 50


class ReflectionEngine:
    """Post-session analysis for continuous self-improvement."""

    def __init__(self, learnings_path: str = LEARNINGS_FILE):
        self.learnings_path = learnings_path
        self._ensure_exists()

    def _ensure_exists(self):
        if not os.path.exists(self.learnings_path):
            os.makedirs(os.path.dirname(self.learnings_path), exist_ok=True)
            with open(self.learnings_path, "w") as f:
                f.write("# ARKA Learnings\n> Accumulated operational wisdom from past sessions.\n\n")

    def get_learnings(self) -> str:
        """Read all learnings."""
        with open(self.learnings_path, "r") as f:
            return f.read()

    def add_learning(self, learning: str, confidence: str = "high") -> str:
        """
        Add a new learning with deduplication.
        
        Args:
            learning: The insight to remember.
            confidence: "high" or "low" — low-confidence learnings are reviewed first.
        """
        # Check for duplicates
        existing = self.get_learnings().lower()
        # Extract core phrase for fuzzy matching
        core = learning.lower().strip()[:50]
        if core in existing:
            return f"Already known: {learning[:60]}..."

        # Check max learnings
        lines = [l for l in existing.split("\n") if l.strip().startswith("- [")]
        if len(lines) >= MAX_LEARNINGS:
            logger.warning("reflection_max_learnings_reached", count=len(lines))
            return f"Max learnings ({MAX_LEARNINGS}) reached. Consider pruning old ones."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"- [{timestamp}] [{confidence}] {learning}\n"
        
        with open(self.learnings_path, "a") as f:
            f.write(entry)
        
        logger.info("reflection_learning_added", learning=learning[:80])
        return f"📝 Learned: {learning}"

    def reflect_on_events(self, events: List[dict]) -> List[str]:
        """
        Analyze a batch of session events and extract learnings.
        Uses heuristic rules (no LLM call to keep it fast and cheap).
        
        Args:
            events: List of event dicts from SQLite.
        
        Returns:
            List of learning strings that were saved.
        """
        learnings_added = []
        
        errors = [e for e in events if e.get("type") == "agent_error"]
        successes = [e for e in events if e.get("type") == "agent_result"]
        user_msgs = [e for e in events if e.get("type") == "user_msg"]
        
        # Learning 1: If there were errors, note what failed
        for err in errors:
            content = err.get("content", "")[:100]
            learning = f"Past error encountered: {content}. Be careful with similar tasks."
            result = self.add_learning(learning, confidence="low")
            if "Learned" in result:
                learnings_added.append(learning)

        # Learning 2: Track success rate
        if successes and errors:
            rate = len(successes) / (len(successes) + len(errors)) * 100
            if rate < 80:
                learning = f"Session success rate was {rate:.0f}%. Review error patterns."
                result = self.add_learning(learning, confidence="low")
                if "Learned" in result:
                    learnings_added.append(learning)

        # Learning 3: Detect frequently mentioned topics
        all_text = " ".join(e.get("content", "") for e in user_msgs).lower()
        if "dark mode" in all_text or "dark theme" in all_text:
            result = self.add_learning("User prefers dark mode/theme.", confidence="high")
            if "Learned" in result:
                learnings_added.append("User prefers dark mode/theme.")

        return learnings_added


# Singleton
reflection_engine = ReflectionEngine()
