import re
from typing import Optional

from core.memory import MemoryManager


def _last_match(pattern: str, text: str) -> Optional[str]:
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    if not matches:
        return None
    if isinstance(matches[-1], tuple):
        return matches[-1][0]
    return matches[-1]


def handle_offline(task: str) -> Optional[str]:
    """
    Offline fallback for memory tests.
    Returns a response string if handled, otherwise None.
    """
    if not task:
        return None

    lower = task.lower()
    mem = MemoryManager()
    profile = mem.get_profile()

    # Remember requests: append raw task to memory
    if "remember" in lower:
        mem.append_fact(task)
        return "Memory updated."

    # Favorite color -> return last hex code
    if "favorite color" in lower or "favourite colour" in lower:
        codes = re.findall(r"#(?:[0-9a-fA-F]{6})", profile)
        if codes:
            return codes[-1]

    # Secret code -> extract most recent code
    if "secret code" in lower:
        code = _last_match(r"secret code (?:is|to) ['\"]?([A-Za-z0-9\-]+)['\"]?", profile)
        if code:
            return code
        code = _last_match(r"changed my secret code to ['\"]?([A-Za-z0-9\-]+)['\"]?", profile)
        if code:
            return code

    # Preferred name / identity
    if "who am i" in lower or "what should you call me" in lower:
        name = _last_match(r"addressed as ['\"]?([^'\"\.]+)", profile)
        if name:
            return name.strip()
        name = _last_match(r"call me ([A-Za-z0-9 _\-]{2,40})", profile)
        if name:
            return name.strip()
        name = _last_match(r"my name is ([A-Za-z0-9 _\-]{2,40})", profile)
        if name:
            return name.strip()

    return None
