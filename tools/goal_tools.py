"""
tools/goal_tools.py — Goal Tools for ARKA (Phase 6.2)

Allows the agent to manage multi-step goals via smolagents tools.
"""

from smolagents import tool
from core.goal_manager import goal_manager
import json


@tool
def set_goal(description: str, steps_json: str) -> str:
    """
    Sets a new multi-step goal for the user.
    Decompose the goal into concrete steps and provide them as a JSON array.
    
    Args:
        description: High-level goal description (e.g., "Deploy my app to production").
        steps_json: JSON array of step strings (e.g., '["Write tests", "Fix lint errors", "Deploy to Vercel"]').
    """
    try:
        steps = json.loads(steps_json)
        if not isinstance(steps, list) or not steps:
            return "Error: steps_json must be a non-empty JSON array of strings."
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON — {e}"
    
    goal = goal_manager.create_goal(description, steps)
    return f"🎯 Goal '{description}' created with {len(steps)} steps (ID: {goal.id})"


@tool
def list_goals() -> str:
    """
    Lists all active goals and their progress.
    """
    active = goal_manager.get_active_goals()
    if not active:
        return "No active goals. Use set_goal to create one."
    
    lines = []
    for g in active:
        lines.append(f"🎯 [{g.id}] {g.description} ({g.progress})")
        for i, step in enumerate(g.steps):
            icon = "✅" if i in g.completed_steps else "⬜"
            lines.append(f"   {icon} {i+1}. {step}")
    return "\n".join(lines)


@tool
def advance_goal(goal_id: str) -> str:
    """
    Marks the next step of a goal as completed and advances progress.
    
    Args:
        goal_id: The ID of the goal to advance (from list_goals output).
    """
    return goal_manager.advance_goal(goal_id)


@tool
def complete_goal(goal_id: str) -> str:
    """
    Marks an entire goal as completed.
    
    Args:
        goal_id: The ID of the goal to complete.
    """
    return goal_manager.complete_goal(goal_id)
