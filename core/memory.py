import os
import datetime
from memory.store import memory_store

class MemoryManager:
    def __init__(self, profile_path="memory/user_profile.md"):
        self.profile_path = profile_path
        self._ensure_exists()

    def _ensure_exists(self):
        if not os.path.exists(self.profile_path):
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, "w") as f:
                f.write("# User Profile & Context\n- Created: " + str(datetime.date.today()) + "\n")

    def get_profile(self) -> str:
        """Reads the full user profile."""
        with open(self.profile_path, "r") as f:
            return f.read()

    def append_fact(self, fact: str) -> str:
        """Appends a new fact with a timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n    - [{timestamp}] {fact}"
        
        # We append to the 'Preferences' section or just end of file if simple
        # For robustness, we just append to end for now
        with open(self.profile_path, "a") as f:
            f.write(entry)
        # Also store in unified memory store (non-upsert to preserve history)
        memory_store.insert_fact(
            subject="user",
            predicate="note",
            obj=fact,
            metadata={"source": "manual_memory"},
        )
            
        return f"Memory updated: {entry.strip()}"
