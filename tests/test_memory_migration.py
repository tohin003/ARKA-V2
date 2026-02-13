import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import memory.migrate as migrate
from memory.store import MemoryStore


def test_migrate_profile_and_learnings():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "mem.db")
        store = MemoryStore(db_path=db_path)

        # Patch migrate module to use temp store
        migrate.memory_store = store

        profile_path = os.path.join(tmp, "user_profile.md")
        with open(profile_path, "w") as f:
            f.write("# User Profile\n- [2024-01-01] Likes dark mode\n")

        learnings_path = os.path.join(tmp, "learnings.md")
        with open(learnings_path, "w") as f:
            f.write("# Learnings\n- [2024-01-01] Be careful with tasks\n")

        added_profile = migrate.migrate_user_profile(profile_path=profile_path)
        added_learnings = migrate.migrate_learnings(learnings_path=learnings_path)

        assert added_profile == 1
        assert added_learnings == 1

        results = store.search_facts("dark mode", limit=5)
        assert results


if __name__ == "__main__":
    test_migrate_profile_and_learnings()
    print("ok")
