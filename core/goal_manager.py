"""
core/goal_manager.py — Goal Persistence (Phase 6.2)

Multi-step autonomy: User sets a high-level goal, ARKA decomposes it
into steps and auto-advances across sessions.

Goals are persisted to ~/.arka/goals.json.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional
import structlog

logger = structlog.get_logger()

GOALS_FILE = os.path.expanduser("~/.arka/goals.json")


class Goal:
    def __init__(self, description: str, steps: List[str] = None, goal_id: str = None):
        self.id = goal_id or str(uuid.uuid4())[:8]
        self.description = description
        self.steps = steps or []
        self.completed_steps: List[int] = []
        self.status = "active"  # active, completed, paused
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "steps": self.steps,
            "completed_steps": self.completed_steps,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        g = cls(data["description"], data.get("steps", []), data.get("id"))
        g.completed_steps = data.get("completed_steps", [])
        g.status = data.get("status", "active")
        g.created_at = data.get("created_at", "")
        return g

    @property
    def next_step(self) -> Optional[str]:
        for i, step in enumerate(self.steps):
            if i not in self.completed_steps:
                return step
        return None

    @property
    def next_step_index(self) -> Optional[int]:
        for i in range(len(self.steps)):
            if i not in self.completed_steps:
                return i
        return None

    @property
    def progress(self) -> str:
        done = len(self.completed_steps)
        total = len(self.steps)
        return f"{done}/{total}"


class GoalManager:
    """Manages persistent goals with multi-step tracking."""

    def __init__(self, goals_file: str = GOALS_FILE):
        self.goals_file = goals_file
        self.goals: List[Goal] = []
        self._load()

    def _load(self):
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, "r") as f:
                    data = json.load(f)
                self.goals = [Goal.from_dict(g) for g in data]
            except Exception:
                self.goals = []

    def _save(self):
        os.makedirs(os.path.dirname(self.goals_file), exist_ok=True)
        with open(self.goals_file, "w") as f:
            json.dump([g.to_dict() for g in self.goals], f, indent=2)

    def create_goal(self, description: str, steps: List[str]) -> Goal:
        """Create a new goal with pre-decomposed steps."""
        goal = Goal(description=description, steps=steps)
        self.goals.append(goal)
        self._save()
        logger.info("goal_created", id=goal.id, steps=len(steps))
        return goal

    def get_active_goals(self) -> List[Goal]:
        return [g for g in self.goals if g.status == "active"]

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        for g in self.goals:
            if g.id == goal_id:
                return g
        return None

    def advance_goal(self, goal_id: str) -> str:
        """Mark next step as completed. Returns status message."""
        goal = self.get_goal(goal_id)
        if not goal:
            return f"Goal {goal_id} not found."
        
        idx = goal.next_step_index
        if idx is None:
            goal.status = "completed"
            self._save()
            return f"🎉 Goal '{goal.description}' is fully complete!"
        
        goal.completed_steps.append(idx)
        
        # Check if all steps are done
        if goal.next_step is None:
            goal.status = "completed"
        
        self._save()
        return f"✅ Step {idx + 1} completed ({goal.progress}): {goal.steps[idx]}"

    def complete_goal(self, goal_id: str) -> str:
        """Mark entire goal as completed."""
        goal = self.get_goal(goal_id)
        if not goal:
            return f"Goal {goal_id} not found."
        goal.status = "completed"
        self._save()
        return f"🎉 Goal '{goal.description}' marked as complete."

    def format_for_prompt(self) -> str:
        """Format active goals for system prompt injection."""
        active = self.get_active_goals()
        if not active:
            return ""
        
        lines = ["## 🎯 ACTIVE GOALS"]
        for g in active:
            lines.append(f"### Goal: {g.description} [{g.progress}]")
            for i, step in enumerate(g.steps):
                icon = "✅" if i in g.completed_steps else "⬜"
                marker = " ← NEXT" if i == g.next_step_index else ""
                lines.append(f"  {icon} {i+1}. {step}{marker}")
        return "\n".join(lines)


# Singleton
goal_manager = GoalManager()
