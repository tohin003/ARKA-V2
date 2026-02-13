import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("ARKA_OFFLINE", "1")
os.environ.setdefault("ARKA_DISABLE_LANGFUSE", "1")

from core.engine import ArkaEngine
from core.session_context import session_context


def test_coding_mode_toggle():
    engine = ArkaEngine()
    assert engine.mode == "default"

    session_context.update_mode("coding")
    engine.run("noop task")
    assert engine.mode == "coding"

    session_context.update_mode("default")
    engine.run("noop task")
    assert engine.mode == "default"


if __name__ == "__main__":
    test_coding_mode_toggle()
    print("ok")
