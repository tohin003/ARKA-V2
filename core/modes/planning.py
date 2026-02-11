from core.engine import ArkaEngine
from core.llm import model_router
from tools.dev import read_file, write_file, grep
from tools.terminal import run_terminal
import structlog
import os

logger = structlog.get_logger()

PLAN_TEMPLATE = """# Implementation Plan - {title}

## Goal
{goal}

## Proposed Changes
- [ ] Change X in `file.py`
- [ ] Add Y to `other.py`

## Verification
- [ ] Run `pytest tests/`
"""

class PlanningMode:
    """
    Handles the "Planning" phase of a task.
    - Doesn't execute code changes (ReadOnly).
    - Interviews the user.
    - Drafts/Updates `implementation_plan.md`.
    """
    def __init__(self, engine: ArkaEngine):
        self.engine = engine
        self.plan_path = os.path.abspath("implementation_plan.md")

    def start_plan(self, user_request: str) -> str:
        """
        Starts a planning session for a request.
        """
        logger.info("plan_mode_start", request=user_request)
        
        # 1. Create initial plan file if missing
        if not os.path.exists(self.plan_path):
            write_file(self.plan_path, PLAN_TEMPLATE.format(title="New Task", goal=user_request))
            
        # 2. Planning Loop (Simplified for V2)
        # In a full UI loop, this would ask questions. 
        # Here we use the Planner Model (gpt-5.2-chat-latest / pro) to analyze requirements.
        
        prompt = f"""
        You are the Architect. The user wants: "{user_request}".
        
        Existing Plan:
        {read_file(self.plan_path)}
        
        Your Job:
        1. Analyze the request.
        2. If ambiguous, list questions to ask.
        3. If clear, rewrite the 'Proposed Changes' section of the plan to be technical and precise.
        
        Return ONLY the updated content for `implementation_plan.md`.
        """
        
        # We use the Planner model directly
        messages = [{"role": "user", "content": prompt}]
        try:
            # OpenAIServerModel.generate returns a ChatMessage object or string content depending on implementation.
            # In smolagents 1.24.0, it typically returns a ChatMessage.
            # GPT-5.2 requires 'max_completion_tokens' instead of 'max_tokens'
            response_msg = model_router.planner.generate(messages=messages, max_completion_tokens=2000)
            
            # Extract content (handle if it's an object or string)
            response_text = response_msg.content if hasattr(response_msg, 'content') else str(response_msg)
            
            # Save updated plan
            write_file(self.plan_path, response_text)
            logger.info("plan_updated")
            
            return f"✅ Plan updated at {self.plan_path}. Please review it."
            
        except Exception as e:
            return f"Planning failed: {str(e)}"

# Singleton factory not needed, instantiated per session usually
