import json
import os
from typing import Dict, List, Optional

from memory.store import memory_store

MIGRATIONS_FILE = os.path.expanduser("~/.arka/memory/migrations.json")


def _load_migrations() -> Dict:
    if not os.path.exists(MIGRATIONS_FILE):
        return {}
    try:
        with open(MIGRATIONS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_migrations(state: Dict) -> None:
    os.makedirs(os.path.dirname(MIGRATIONS_FILE), exist_ok=True)
    with open(MIGRATIONS_FILE, "w") as f:
        json.dump(state, f, indent=2)


def _parse_bullets(lines: List[str]) -> List[str]:
    items: List[str] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("-"):
            continue
        # Remove leading '-' and timestamp pattern
        cleaned = line.lstrip("-").strip()
        if cleaned.startswith("["):
            # Remove leading [timestamp] if present
            closing = cleaned.find("]")
            if closing != -1:
                cleaned = cleaned[closing + 1 :].strip()
        if cleaned:
            items.append(cleaned)
    return items


def migrate_user_profile(profile_path: str = "memory/user_profile.md") -> int:
    if not os.path.exists(profile_path):
        return 0
    with open(profile_path, "r") as f:
        lines = f.readlines()
    entries = _parse_bullets(lines)
    added = 0
    for entry in entries:
        if memory_store.insert_fact(
            subject="user",
            predicate="note",
            obj=entry,
            metadata={"source": "v2_user_profile"},
        ):
            added += 1
    return added


def migrate_learnings(learnings_path: str = "memory/learnings.md") -> int:
    if not os.path.exists(learnings_path):
        return 0
    with open(learnings_path, "r") as f:
        lines = f.readlines()
    entries = _parse_bullets(lines)
    added = 0
    for entry in entries:
        if memory_store.insert_fact(
            subject="system",
            predicate="learning",
            obj=entry,
            metadata={"source": "v2_learnings"},
        ):
            added += 1
    return added


def migrate_v1_json(v1_path: Optional[str] = None) -> int:
    if not v1_path:
        v1_path = os.path.expanduser("~/.arka/memory/memories.json")
    if not os.path.exists(v1_path):
        return 0
    try:
        with open(v1_path, "r") as f:
            data = json.load(f)
    except Exception:
        return 0

    added = 0
    for _, entry in data.items():
        content = entry.get("content", "").strip()
        meta = entry.get("metadata", {})
        if not content:
            continue
        if meta.get("type") == "persona":
            fact_id = memory_store.upsert_fact(
                subject="user",
                predicate="persona",
                obj=content,
                metadata={"source": "v1_memory", "node": meta.get("node")},
            )
        else:
            fact_id = memory_store.insert_fact(
                subject="user",
                predicate="note",
                obj=content,
                metadata={"source": "v1_memory", "node": meta.get("node")},
            )
        if fact_id:
            added += 1
    return added


def run_all_migrations() -> Dict[str, int]:
    state = _load_migrations()
    results = {"profile": 0, "learnings": 0, "v1": 0}

    if not state.get("migrated_user_profile"):
        results["profile"] = migrate_user_profile()
        state["migrated_user_profile"] = True

    if not state.get("migrated_learnings"):
        results["learnings"] = migrate_learnings()
        state["migrated_learnings"] = True

    if not state.get("migrated_v1_json"):
        results["v1"] = migrate_v1_json()
        state["migrated_v1_json"] = True

    _save_migrations(state)
    return results
