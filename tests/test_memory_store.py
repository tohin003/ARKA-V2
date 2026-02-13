import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.store import MemoryStore


def test_memory_store_basic():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "mem.db")
        store = MemoryStore(db_path=db_path)

        event_id = store.add_event("s1", "user_msg", "hello")
        assert event_id is not None

        fact_id = store.upsert_fact("user", "preferred_name", "Commander", confidence=0.9)
        assert fact_id is not None

        note_id = store.insert_fact("user", "note", "Likes dark mode")
        assert note_id is not None
        assert note_id != fact_id

        results = store.search_facts("Commander", limit=5)
        assert results
        assert any(r["object"] == "Commander" for r in results)

        lock_ok = store.mark_fact_locked(fact_id, locked=True)
        assert lock_ok is True

        ep_id = store.add_episode("s1", "User asked about memory")
        assert ep_id is not None

        stats = store.stats()
        assert stats["facts"] >= 2
        assert stats["events"] >= 1
        assert stats["episodes"] >= 1

        export_path = os.path.join(tmp, "export.json")
        exported = store.export_facts(export_path)
        assert os.path.exists(exported)


if __name__ == "__main__":
    test_memory_store_basic()
    print("ok")
