import re
from typing import Dict, List

from memory.config import SAFE_PREDICATES, SENSITIVE_KEYWORDS
from memory.store import MemoryStore


def _clean_value(value: str) -> str:
    value = value.strip()
    value = value.strip('"\'')
    value = value.strip()
    # Normalize multiple spaces
    value = re.sub(r"\s+", " ", value)
    return value


def extract_facts_from_text(text: str) -> List[Dict[str, str]]:
    """Extract safe, low-risk facts from user text."""
    if not text:
        return []

    facts: List[Dict[str, str]] = []
    lower = text.lower()

    # Skip if text appears to contain sensitive data
    if any(keyword in lower for keyword in SENSITIVE_KEYWORDS):
        return []

    patterns = [
        (r"\bcall me ([A-Za-z0-9 _\-]{2,40})", "preferred_name"),
        (r"\bi go by ([A-Za-z0-9 _\-]{2,40})", "preferred_name"),
        (r"\bmy name is ([A-Za-z0-9 _\-]{2,40})", "name"),
        (r"\bi am ([A-Za-z0-9 _\-]{2,40})", "name"),
        (r"\bmy pronouns are ([A-Za-z/ ]{2,40})", "pronouns"),
        (r"\bi prefer (.+)$", "preference"),
        (r"\bi like (.+)$", "preference"),
        (r"\bi love (.+)$", "preference"),
        (r"\bi use (.+)$", "preference"),
    ]

    for pattern, predicate in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        value = _clean_value(match.group(1))
        if not value:
            continue
        if predicate not in SAFE_PREDICATES:
            continue
        # Truncate very long values
        if len(value) > 120:
            value = value[:120]
        facts.append({"subject": "user", "predicate": predicate, "object": value})

    # Theme preferences (explicit keywords)
    if "dark mode" in lower or "dark theme" in lower:
        facts.append({"subject": "user", "predicate": "theme", "object": "dark"})
    if "light mode" in lower or "light theme" in lower:
        facts.append({"subject": "user", "predicate": "theme", "object": "light"})

    return facts


def distill_user_text(store: MemoryStore, event_id: int, text: str) -> int:
    """Extract facts from text and upsert into memory. Returns count added."""
    facts = extract_facts_from_text(text)
    added = 0
    for f in facts:
        fact_id = store.upsert_fact(
            subject=f["subject"],
            predicate=f["predicate"],
            obj=f["object"],
            confidence=0.8,
            source_event_id=event_id,
            metadata={"source": "auto_distiller"},
        )
        if fact_id:
            added += 1
    return added
