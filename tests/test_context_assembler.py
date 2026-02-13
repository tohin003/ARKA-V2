import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory.context import ContextAssembler
import memory.context as context_module
from memory.store import MemoryStore


def test_context_assembler_builds_memory_block():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "mem.db")
        store = MemoryStore(db_path=db_path)
        store.upsert_fact("user", "preferred_name", "Commander")
        store.add_episode("s1", "User asked to remember preferences")

        # Patch module-level singleton for this test
        context_module.memory_store = store

        assembler = ContextAssembler()
        block = assembler.build("What should you call me?")
        assert "RETRIEVED MEMORY" in block
        assert "Commander" in block


if __name__ == "__main__":
    test_context_assembler_builds_memory_block()
    print("ok")
