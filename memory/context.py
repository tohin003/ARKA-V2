import os
from typing import List

from memory.config import (
    INCLUDE_SENSITIVE_DEFAULT,
    INCLUDE_SENSITIVE_ENV,
    RECALL_MAX_EPISODES,
    RECALL_MAX_FACTS,
    RECALL_MAX_TOKENS,
)
from memory.store import memory_store


def _estimate_tokens(text: str) -> int:
    # Rough heuristic: ~4 chars per token
    if not text:
        return 0
    return max(1, len(text) // 4)


class ContextAssembler:
    def __init__(self):
        pass

    def build(self, task: str, max_tokens: int = RECALL_MAX_TOKENS) -> str:
        if not task:
            return ""

        include_sensitive = os.getenv(INCLUDE_SENSITIVE_ENV, INCLUDE_SENSITIVE_DEFAULT) == "1"

        facts = memory_store.search_facts(task, limit=RECALL_MAX_FACTS)
        if not facts:
            facts = memory_store.get_recent_facts(limit=RECALL_MAX_FACTS)

        facts = self._filter_facts(facts, include_sensitive)
        episodes = memory_store.get_recent_episodes(limit=RECALL_MAX_EPISODES)

        lines: List[str] = ["## 🧠 RETRIEVED MEMORY"]
        tokens = _estimate_tokens(lines[0])

        if facts:
            lines.append("### Facts")
            tokens += _estimate_tokens(lines[-1])
            for fact in facts:
                line = self._format_fact(fact)
                line_tokens = _estimate_tokens(line)
                if tokens + line_tokens > max_tokens:
                    break
                lines.append(line)
                tokens += line_tokens

        if episodes:
            lines.append("### Recent Episodes")
            tokens += _estimate_tokens(lines[-1])
            for ep in episodes:
                line = f"- {ep.get('summary', '').strip()}"
                line_tokens = _estimate_tokens(line)
                if tokens + line_tokens > max_tokens:
                    break
                lines.append(line)
                tokens += line_tokens

        if len(lines) <= 1:
            return ""
        return "\n".join(lines)

    def _filter_facts(self, facts: List[dict], include_sensitive: bool) -> List[dict]:
        filtered = []
        for f in facts:
            meta = f.get("metadata") or {}
            if not include_sensitive and meta.get("sensitive"):
                continue
            if f.get("is_deleted"):
                continue
            filtered.append(f)
        return filtered

    def _format_fact(self, fact: dict) -> str:
        subj = fact.get("subject", "?")
        pred = fact.get("predicate", "?")
        obj = fact.get("object", "?")
        return f"- {subj}.{pred}: {obj}"


# Singleton
context_assembler = ContextAssembler()
