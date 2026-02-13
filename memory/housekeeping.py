import json
import os
from datetime import datetime, timedelta
from typing import Dict

from memory.config import (
    DEFAULT_EVENT_TTL_DAYS,
    DEFAULT_EPISODE_TTL_DAYS,
    HOUSEKEEPING_INTERVAL_HOURS,
)
from memory.store import memory_store

STATE_FILE = os.path.expanduser("~/.arka/memory/housekeeping.json")


def _load_state() -> Dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: Dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def should_run() -> bool:
    state = _load_state()
    last_run = state.get("last_run")
    if not last_run:
        return True
    try:
        last_dt = datetime.fromisoformat(last_run)
    except Exception:
        return True
    return datetime.now() - last_dt >= timedelta(hours=HOUSEKEEPING_INTERVAL_HOURS)


def run_cleanup(force: bool = False) -> Dict[str, int]:
    if not force and not should_run():
        return {"events_deleted": 0, "facts_expired": 0, "episodes_deleted": 0}

    events_deleted = memory_store.cleanup_events(DEFAULT_EVENT_TTL_DAYS)
    facts_expired = memory_store.cleanup_expired_facts()
    episodes_deleted = memory_store.cleanup_episodes(DEFAULT_EPISODE_TTL_DAYS)

    _save_state({"last_run": datetime.now().isoformat()})

    return {
        "events_deleted": events_deleted,
        "facts_expired": facts_expired,
        "episodes_deleted": episodes_deleted,
    }
