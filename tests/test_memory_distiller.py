import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.distiller import distill_user_text
from memory.store import MemoryStore


def test_distiller_extracts_facts():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "mem.db")
        store = MemoryStore(db_path=db_path)

        event_id = store.add_event("s1", "user_msg", "Call me Commander")
        assert event_id is not None

        added = distill_user_text(store, event_id, "Call me Commander")
        assert added >= 1

        results = store.search_facts("Commander", limit=5)
        assert results


if __name__ == "__main__":
    test_distiller_extracts_facts()
    print("ok")
