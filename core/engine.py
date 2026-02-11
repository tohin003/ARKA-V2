from smolagents import CodeAgent
from core.llm import model_router
from memory.db import memory_client
from memory.mistakes import mistake_guard
import structlog
import uuid

logger = structlog.get_logger()

class ArkaEngine(CodeAgent):
    """
    The Core Engine of ARKA V2.
    Extends smolagents.CodeAgent to add our specific intelligence stack.
    """
    def __init__(self, tools=None, additional_imports=None):
        if not model_router:
            raise RuntimeError("ModelRouter unavailable. Cannot start ArkaEngine.")
        
        # Import God Mode tools dynamically to avoid circular deps if needed
        from tools.hardware import music_control, set_volume, wifi_control, bluetooth_control
        from tools.system import system_click, system_type, open_app
        from tools.vision import get_screen_coordinates
        from tools.browser import visit_page
        from tools.todo import todo_add, todo_list, todo_complete
        from tools.codebase_graph import generate_graph
        from tools.search import web_search
        from tools.messaging import send_whatsapp_message
        from tools.memory_tools import remember_fact
        from tools.mcp_tools import list_mcp_tools, call_mcp_tool
        from tools.goal_tools import set_goal, list_goals, advance_goal, complete_goal
        
        # We start with a basic toolset + God Mode tools
        base_tools = tools or []
        god_mode_tools = [
            music_control, set_volume, wifi_control, bluetooth_control,
            system_click, system_type, open_app,
            get_screen_coordinates,
            visit_page,
            todo_add, todo_list, todo_complete,
            generate_graph,
            web_search,
            send_whatsapp_message,
            remember_fact,
            list_mcp_tools, call_mcp_tool,
            set_goal, list_goals, advance_goal, complete_goal
        ]
        agent_tools = base_tools + god_mode_tools
        
        # Configure safe imports (we will add more in Phase 2 for God Mode)
        safe_imports = [
            "structlog", "datetime", "json", "re", "math", "random", "os", "sys"
        ]
        if additional_imports:
            safe_imports.extend(additional_imports)

        # Define strict system prompt
        system_prompt = """
        You are ARKA V2, a God Mode Agent for macOS.
        Your primary directive is PRECISE EXECUTION.
        
        CRITICAL RULES:
        1. When invoking tools, use the EXACT parameters provided by the user. 
           Do NOT synonymize, paraphrase, or hallucinate different values.
           Example: If user says "Play Breakup Party", you MUST call music_control(song_name="Breakup Party").
           DO NOT change it to "Since U Been Gone" or any other song.
           
        2. PARSING "SEND MESSAGE" COMMANDS:
           - Pattern: "Send [Message] to [Contact]"
           - Strategy: The Contact Name is usually at the END. 
           - Example: "Send hello world to Paad" -> contact_name="Paad", message="hello world"
           - Example: "Send I am Arka to Paad" -> contact_name="Paad", message="I am Arka"
           - ALWAYS call `send_whatsapp_message` for WhatsApp requests.
           
        3. If a command is ambiguous, choose the LITERAL interpretation (Exact String Match) over a generic/semantic one.
        
        4. Solve tasks step-by-step.
        """
        
        super().__init__(
            tools=agent_tools,
            model=model_router.executor, # use the Codex model for actions
            add_base_tools=False, # File/Search tools from base (Disabled to avoid ddgs dependency issue)
            max_steps=20,
            verbosity_level=1,
            additional_authorized_imports=safe_imports,
            planning_interval=None # Disable planning for now to be direct
        )
        
        # Initialize Memory (The Cortex)
        from core.memory import MemoryManager
        self.semantic_memory = MemoryManager()
        
        # Inject Memory into System Prompt
        user_context = self.semantic_memory.get_profile()
        memory_injection = f"""
        
## 🧠 SEMANTIC MEMORY (USER PROFILE)
The following is your Long-Term Memory about the User. Use this to personalize every interaction.
{user_context}
"""
        
        # Inject Learnings (Phase 6.3 - Reflection)
        from core.reflection import reflection_engine
        self.reflection = reflection_engine
        learnings = self.reflection.get_learnings()
        learnings_injection = f"""
## 📚 OPERATIONAL LEARNINGS
These are lessons learned from past sessions. Apply them.
{learnings}
"""
        
        # Inject Active Goals (Phase 6.2)
        from core.goal_manager import goal_manager
        self.goal_manager = goal_manager
        goals_injection = goal_manager.format_for_prompt()
        
        # Build complete system prompt
        self.prompt_templates["system_prompt"] = (
            system_prompt + memory_injection + learnings_injection + 
            goals_injection + self.prompt_templates.get("system_prompt", "")
        )
        
        # Initialize Context Sensor and Tone Adapter (Phase 6.4, 6.5)
        from core.context_sensor import context_sensor
        from core.tone_adapter import tone_adapter
        self._context_sensor = context_sensor
        self._tone_adapter = tone_adapter
        
        logger.info("ArkaEngine_Initialized", model=model_router.executor_id, tools=len(agent_tools))

    def run(self, task: str, *args, **kwargs):
        # Generate Session ID
        session_id = str(uuid.uuid4())
        logger.info("agent_run_start", session_id=session_id, task=task)
        
        # 1. Log Task to DB
        memory_client.log_event(session_id, "user_msg", task)
        
        # 2. MistakeGuard: Check if the task itself is malicious (basic check)
        safety_error = mistake_guard.validate_command(task)
        if safety_error:
            from observability.logger import log_event
            log_event("run_blocked_safety", error=safety_error)
            return f"❌ {safety_error}"

        # 3. Inject Live Context (Phase 6.4) + Tone (Phase 6.5)
        context_str = self._context_sensor.format_for_prompt()
        tone_str = self._tone_adapter.detect_tone(task)
        augmented_task = task
        if context_str or tone_str:
            augmented_task = f"{context_str}\n{tone_str}\nUSER REQUEST: {task}"

        try:
            # Execute with augmented task
            result = super().run(augmented_task, *args, **kwargs)
            
            # 4. Log Result
            memory_client.log_event(session_id, "agent_result", str(result))
            
            from observability.logger import log_event
            log_event("agent_run_success", result=str(result)[:100])
            
            return result
        except Exception as e:
            error_msg = str(e)
            memory_client.log_event(session_id, "agent_error", error_msg)
            
            # 5. Reflect on errors (Phase 6.3)
            try:
                events = memory_client.get_session_history(session_id)
                self.reflection.reflect_on_events(events)
            except Exception:
                pass  # Don't let reflection failure crash the agent
            
            from observability.logger import log_event
            log_event("agent_run_failed", error=error_msg)
            raise e
