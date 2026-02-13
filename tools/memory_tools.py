import os
import json

from smolagents import tool
from core.memory import MemoryManager
from memory.store import memory_store


@tool
def remember_fact(fact: str) -> str:
    """
    Learns a new fact about the user or the system and saves it to long-term memory.
    Use this proactively when the user states a preference (e.g., "I like dark mode", "My API key is X").
    
    Args:
        fact: The fact to remember (e.g., "User prefers Python over JS").
    """
    memory = MemoryManager()
    result = memory.append_fact(fact)
    return result


@tool
def memory_search(query: str, limit: int = 5) -> str:
    """
    Search long-term memory facts.

    Args:
        query: Search query string.
        limit: Maximum number of results.
    """
    results = memory_store.search_facts(query, limit=limit)
    if not results:
        return "No matching memories found."
    lines = ["Memory matches:"]
    for r in results:
        lines.append(f"- {r.get('id')}: {r.get('subject')}.{r.get('predicate')} = {r.get('object')}")
    return "\n".join(lines)


@tool
def memory_list(limit: int = 20) -> str:
    """
    List most recent memory facts.

    Args:
        limit: Maximum number of facts.
    """
    results = memory_store.get_recent_facts(limit=limit)
    if not results:
        return "No memories found."
    lines = ["Recent memories:"]
    for r in results:
        lines.append(f"- {r.get('id')}: {r.get('subject')}.{r.get('predicate')} = {r.get('object')}")
    return "\n".join(lines)


@tool
def memory_show(fact_id: int) -> str:
    """
    Show a memory fact by ID.

    Args:
        fact_id: ID of the fact to show.
    """
    fact = memory_store.get_fact_by_id(fact_id, include_deleted=True)
    if not fact:
        return "Memory not found."
    deleted = " (deleted)" if fact.get("is_deleted") else ""
    meta = fact.get("metadata") or {}
    lines = [
        f"Memory {fact.get('id')}{deleted}",
        f"Subject: {fact.get('subject')}",
        f"Predicate: {fact.get('predicate')}",
        f"Object: {fact.get('object')}",
        f"Confidence: {fact.get('confidence')}",
        f"Locked: {bool(fact.get('locked'))}",
        f"Created: {fact.get('created_at')}",
        f"Updated: {fact.get('updated_at')}",
        f"Expires: {fact.get('expires_at')}",
    ]
    if meta:
        lines.append(f"Metadata: {meta}")
    return "\n".join(lines)


@tool
def memory_import(path: str) -> str:
    """
    Import memory facts from a JSON file (list of objects with subject/predicate/object).

    Args:
        path: Path to JSON file.
    """
    path = path.replace("~", os.path.expanduser("~"))
    if not os.path.exists(path):
        return f"File not found: {path}"
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return f"Failed to read JSON: {e}"
    if not isinstance(data, list):
        return "Import expects a JSON array of fact objects."
    imported = 0
    skipped = 0
    for item in data:
        if not isinstance(item, dict):
            skipped += 1
            continue
        subject = item.get("subject")
        predicate = item.get("predicate")
        obj = item.get("object")
        if not (subject and predicate and obj):
            skipped += 1
            continue
        confidence = float(item.get("confidence", 0.6))
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else None
        fact_id = memory_store.insert_fact(
            subject=subject,
            predicate=predicate,
            obj=obj,
            confidence=confidence,
            source_event_id=item.get("source_event_id"),
            ttl_days=None,
            metadata=metadata,
        )
        if fact_id:
            imported += 1
            if item.get("locked"):
                memory_store.mark_fact_locked(int(fact_id), locked=True)
        else:
            skipped += 1
    return f"Imported {imported} facts. Skipped {skipped}."


@tool
def memory_purge(older_than_days: int | None = None) -> str:
    """
    Purge expired memories or those older than N days.

    Args:
        older_than_days: If provided, delete facts older than this.
    """
    if older_than_days is None:
        count = memory_store.cleanup_expired_facts()
        return f"Purged {count} expired facts."
    count = memory_store.purge_facts_older_than(int(older_than_days))
    return f"Purged {count} facts older than {older_than_days} days."


@tool
def memory_forget(fact_id: int) -> str:
    """
    Mark a memory fact as deleted by ID.

    Args:
        fact_id: ID of the fact to delete.
    """
    ok = memory_store.mark_fact_deleted(fact_id, reason="user_request")
    return "Memory deleted." if ok else "Failed to delete memory."


@tool
def memory_lock(fact_id: int) -> str:
    """
    Prevent a memory fact from auto-deletion by locking it.

    Args:
        fact_id: ID of the fact to lock.
    """
    ok = memory_store.mark_fact_locked(fact_id, locked=True)
    return "Memory locked." if ok else "Failed to lock memory."


@tool
def memory_export(path: str = "~/.arka/memory/memory_export.json") -> str:
    """
    Export all active memory facts to a JSON file.

    Args:
        path: Output file path.
    """
    path = path.replace("~", os.path.expanduser("~"))
    exported = memory_store.export_facts(path, include_deleted=False)
    return f"Exported memory to {exported}"


@tool
def memory_stats() -> str:
    """
    Show memory store counts.
    """
    stats = memory_store.stats()
    return f"Facts: {stats['facts']}, Events: {stats['events']}, Episodes: {stats['episodes']}"
