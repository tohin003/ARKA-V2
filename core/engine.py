import os

from smolagents import CodeAgent
from smolagents.monitoring import LogLevel
from smolagents.memory import ActionStep
from core.llm import model_router
from memory.db import memory_client
from memory.store import memory_store
from memory.context import context_assembler
from memory.config import RECALL_ENV, RECALL_DEFAULT
from core.offline_mode import handle_offline
from core.intent_router import try_handle as deterministic_try_handle
from core.session_context import session_context
from core.verification import adjust_final_answer, build_evidence
import json
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
        from tools.system import system_click, system_click_at, system_type, open_app
        from tools.vision import get_screen_coordinates, find_text_on_screen, find_and_click_text_on_screen
        from tools.browser import visit_page
        from tools.todo import todo_add, todo_list, todo_complete
        from tools.codebase_graph import generate_graph
        from tools.search import web_search
        from tools.messaging import send_whatsapp_message, send_whatsapp_web_message
        from tools.memory_tools import (
            remember_fact,
            memory_search,
            memory_list,
            memory_show,
            memory_import,
            memory_purge,
            memory_forget,
            memory_lock,
            memory_export,
            memory_stats,
        )
        from tools.mcp_tools import list_mcp_tools, call_mcp_tool
        from tools.goal_tools import set_goal, list_goals, advance_goal, complete_goal
        from tools.chrome_tools import (
            chrome_navigate, chrome_status, chrome_wait_for_connection, chrome_click, chrome_click_at, chrome_focus, chrome_press_key, chrome_wait_for_selector, chrome_type, chrome_scroll, chrome_verify_text,
            chrome_screenshot, chrome_get_dom, chrome_get_text, chrome_get_elements,
            chrome_list_tabs, chrome_new_tab, chrome_switch_tab, chrome_continue
        )
        
        # We start with a basic toolset + God Mode tools
        base_tools = tools or []
        god_mode_tools = [
            music_control, set_volume, wifi_control, bluetooth_control,
            system_click, system_click_at, system_type, open_app,
            get_screen_coordinates, find_text_on_screen, find_and_click_text_on_screen,
            visit_page,
            todo_add, todo_list, todo_complete,
            generate_graph,
            web_search,
            send_whatsapp_message, send_whatsapp_web_message,
            remember_fact,
            memory_search,
            memory_list,
            memory_show,
            memory_import,
            memory_purge,
            memory_forget,
            memory_lock,
            memory_export,
            memory_stats,
            list_mcp_tools, call_mcp_tool,
            set_goal, list_goals, advance_goal, complete_goal,
            chrome_navigate, chrome_status, chrome_wait_for_connection, chrome_click, chrome_click_at, chrome_focus, chrome_press_key, chrome_wait_for_selector, chrome_type, chrome_scroll, chrome_verify_text,
            chrome_screenshot, chrome_get_dom, chrome_get_text, chrome_get_elements,
            chrome_list_tabs, chrome_new_tab, chrome_switch_tab, chrome_continue
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
           - If user requests **browser/web/whatsapp.com**, use `send_whatsapp_web_message`.
           - Otherwise use `send_whatsapp_message` (desktop app).
           - If user names multiple contacts (e.g., "A and B" or "A, B"), send one-by-one.
           
        3. If a command is ambiguous, choose the LITERAL interpretation (Exact String Match) over a generic/semantic one.
        
        4. Solve tasks step-by-step.

        5. WEB BROWSING RULES:
           - For web tasks requiring DOM access, precise clicks, or exact typing, use chrome_* tools.
           - chrome_* tools ONLY work with Google Chrome + the ARKA extension. They do NOT control other browsers.
           - If the user requests a non-Chrome browser (e.g., Comet, Safari), ask to use Chrome for precision.
           - Use system_click/system_type only as a fallback when chrome_* is unavailable.
           - If the user mentions "browser", "tab", "YouTube", or "website", prefer chrome_* tools over music_control/system_*.
           - After launching Chrome, call chrome_wait_for_connection() before DOM actions.
           - Do NOT claim success unless a follow-up check verifies it (e.g., chrome_wait_for_selector on expected results, or chrome_get_text/URL contains expected content).
           - If a chrome_* call returns an error, stop and report it.
           - Do not print raw DOM/text dumps. Keep responses concise.
           - For actions that send/comment/share/DM, use chrome_verify_text to confirm the text appears before claiming success.

        6. NATIVE APP UI RULES:
           - If the user references visible UI (e.g., "top section", "that song", "left side"), use vision tools.
           - Use `find_text_on_screen(query, region_hint)` to locate text (e.g., a song name) and confirm it's visible.
           - Prefer `find_and_click_text_on_screen(query, region_hint)` when the user asks you to select a visible item.
           - If you have coordinates, use `system_click_at(x, y)` to click.
           - Otherwise use `get_screen_coordinates(description)` then click.
           - Apple Music: when searching for a song, check the TOP SECTION first (best match appears there).
        """

        coding_prompt = """
        You are ARKA in CODING MODE. You are a senior software engineer that builds high-quality, production-ready software.

        CODING RULES:
        1. Clarify ambiguous requirements before coding. Ask concise questions if needed.
        2. Prefer minimal, correct diffs. Do not refactor unrelated code.
        3. Follow repo conventions and existing patterns. Keep style consistent.
        4. Use the fastest safe approach: search with rg, edit with apply_patch, avoid manual retyping.
        5. Add or update tests when behavior changes. Run relevant tests if possible.
        6. If you cannot run tests, say so and explain the risk.
        7. Avoid placeholders. Implement the full solution.
        8. Provide a clear summary and list of tests run.
        9. If UI context is referenced, use vision tools to inspect the screen before asking clarifying questions.
        """
        
        from core.step_callbacks import summarize_action_step

        super().__init__(
            tools=agent_tools,
            model=model_router.executor, # use the Codex model for actions
            add_base_tools=False, # File/Search tools from base (Disabled to avoid ddgs dependency issue)
            max_steps=20,
            verbosity_level=LogLevel.ERROR,
            additional_authorized_imports=safe_imports,
            planning_interval=None, # Disable planning for now to be direct
            use_structured_outputs_internally=True,
            step_callbacks={
                # Compact step summary after each action
                ActionStep: summarize_action_step,
            },
        )
        
        # Initialize Memory (The Cortex)
        from core.memory import MemoryManager
        self.semantic_memory = MemoryManager()
        
        # Base prompts
        self._base_prompt_default = system_prompt
        self._base_prompt_coding = coding_prompt

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
        self.mode = "default"
        self._base_prompt_suffix = self.prompt_templates.get("system_prompt", "")
        self.prompt_templates["system_prompt"] = (
            self._base_prompt_default + memory_injection + learnings_injection +
            goals_injection + self._base_prompt_suffix
        )
        
        # Initialize Context Sensor and Tone Adapter (Phase 6.4, 6.5)
        from core.context_sensor import context_sensor
        from core.tone_adapter import tone_adapter
        self._context_sensor = context_sensor
        self._tone_adapter = tone_adapter
        
        logger.info("ArkaEngine_Initialized", model=model_router.executor_id, tools=len(agent_tools))

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Compose the final system prompt with memory, learnings, and goals."""
        user_context = self.semantic_memory.get_profile()
        memory_injection = f"""

## 🧠 SEMANTIC MEMORY (USER PROFILE)
The following is your Long-Term Memory about the User. Use this to personalize every interaction.
{user_context}
"""

        learnings = self.reflection.get_learnings()
        learnings_injection = f"""
## 📚 OPERATIONAL LEARNINGS
These are lessons learned from past sessions. Apply them.
{learnings}
"""

        goals_injection = self.goal_manager.format_for_prompt()
        return base_prompt + memory_injection + learnings_injection + goals_injection + self._base_prompt_suffix

    def set_mode(self, mode: str) -> str:
        """Switch agent mode and update model/system prompt."""
        mode = (mode or "").strip().lower()
        if mode not in {"default", "coding"}:
            return f"Unknown mode: {mode}"

        if self.mode == mode:
            return f"Mode already set to {mode}."

        self.mode = mode
        if mode == "coding":
            if model_router and getattr(model_router, "coding_executor", None):
                self.model = model_router.coding_executor
            self.prompt_templates["system_prompt"] = self._build_system_prompt(self._base_prompt_coding)
            return "Coding mode enabled."

        # default mode
        if model_router and getattr(model_router, "executor", None):
            self.model = model_router.executor
        self.prompt_templates["system_prompt"] = self._build_system_prompt(self._base_prompt_default)
        return "Default mode enabled."

    def _route_task(self, task: str) -> dict:
        """Use router model to resolve intent and ambiguity."""
        fallback = {
            "resolved_task": task,
            "requires_clarification": False,
            "clarifying_question": "",
            "domain": "general",
            "needs_planning": False,
            "requires_verification": False,
        }

        if not model_router or not getattr(model_router, "router", None):
            return fallback

        router_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "RouterResult",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "resolved_task": {"type": "string"},
                        "requires_clarification": {"type": "boolean"},
                        "clarifying_question": {"type": "string"},
                        "domain": {"type": "string"},
                        "needs_planning": {"type": "boolean"},
                        "requires_verification": {"type": "boolean"},
                    },
                    "required": [
                        "resolved_task",
                        "requires_clarification",
                        "clarifying_question",
                        "domain",
                        "needs_planning",
                        "requires_verification",
                    ],
                },
            },
        }

        prompt = (
            "You are a router that resolves user intent and ambiguity.\n"
            "Return a JSON object only.\n\n"
            f"Session context:\n{session_context.format_for_prompt()}\n\n"
            f"User task:\n{task}\n"
        )
        try:
            msg = model_router.router.generate(
                messages=[{"role": "user", "content": prompt}],
                response_format=router_schema,
                max_completion_tokens=300,
            )
            content = msg.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to recover JSON from a larger string
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    return json.loads(content[start : end + 1])
        except Exception:
            return fallback

        return fallback

    def _verify_result(self, task: str, final_answer: str) -> str:
        """Strict verification using verifier model + evidence."""
        if not model_router or not getattr(model_router, "verifier", None):
            return final_answer

        verifier_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "VerifierResult",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "verdict": {"type": "string"},
                        "should_claim_success": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["verdict", "should_claim_success", "reason"],
                },
            },
        }

        evidence = build_evidence(self.memory)
        prompt = (
            "You are a strict verifier. Decide if the task was verified.\n"
            "Rules: If there is no explicit verification, do NOT allow success claims.\n"
            "Return JSON only.\n\n"
            f"Task: {task}\n"
            f"Final answer: {final_answer}\n"
            f"Evidence:\n{evidence}\n"
        )
        try:
            msg = model_router.verifier.generate(
                messages=[{"role": "user", "content": prompt}],
                response_format=verifier_schema,
                max_completion_tokens=300,
            )
            content = msg.content
            data = json.loads(content) if content else None
            if not data:
                return final_answer
            if data.get("should_claim_success") is False:
                return data.get("reason") or "I couldn't verify success. Please confirm."
            return final_answer
        except Exception:
            return final_answer

    def run(self, task: str, *args, **kwargs):
        # Generate Session ID
        session_id = str(uuid.uuid4())
        logger.info("agent_run_start", session_id=session_id, task=task)

        # Update session context
        resolved_task = session_context.resolve_task(task)
        session_context.update_task(resolved_task)

        # Sync mode with session context
        if session_context.mode and session_context.mode != self.mode:
            self.set_mode(session_context.mode)

        # Offline mode short-circuit (for local tests)
        if os.getenv("ARKA_OFFLINE", "0") == "1":
            memory_client.log_event(session_id, "user_msg", task)
            response = handle_offline(resolved_task)
            if response is None:
                response = "OFFLINE_MODE: unable to handle request."
            memory_client.log_event(session_id, "agent_result", str(response))
            try:
                summary = f"User asked: {resolved_task} | Result: {str(response)[:120]}"
                memory_store.add_episode(session_id=session_id, summary=summary)
            except Exception:
                pass
            return response

        # Deterministic intent router (bypass LLM when confident)
        memory_client.log_event(session_id, "user_msg", task)
        deterministic_result = deterministic_try_handle(resolved_task)
        if deterministic_result:
            memory_client.log_event(session_id, "agent_result", str(deterministic_result))
            try:
                summary = f"User asked: {resolved_task} | Result: {str(deterministic_result)[:120]}"
                memory_store.add_episode(session_id=session_id, summary=summary)
            except Exception:
                pass
            return deterministic_result

        # Router pass (accuracy > latency)
        route = self._route_task(resolved_task)
        if route.get("requires_clarification") and route.get("clarifying_question"):
            return route["clarifying_question"]
        resolved_task = route.get("resolved_task") or resolved_task
        
        # 1. Log Task to DB (already logged above)
        
        # 2. MistakeGuard: Check if the task itself is malicious (basic check)
        safety_error = mistake_guard.validate_command(task)
        if safety_error:
            from observability.logger import log_event
            log_event("run_blocked_safety", error=safety_error)
            return f"❌ {safety_error}"

        # 3. Inject Live Context (Phase 6.4) + Session Context + Tone (Phase 6.5)
        context_str = self._context_sensor.format_for_prompt()
        session_str = session_context.format_for_prompt()
        ref_str = session_context.reference_hint(resolved_task)
        ui_hint = session_context.ui_reference_hint(resolved_task)
        tone_str = self._tone_adapter.detect_tone(resolved_task)
        memory_str = ""
        if os.getenv(RECALL_ENV, RECALL_DEFAULT) == "1":
            memory_str = context_assembler.build(resolved_task)
        router_directive = (
            f"## 🧭 ROUTER DIRECTIVE\n"
            f"- Domain: {route.get('domain','general')}\n"
            f"- Needs planning: {route.get('needs_planning', False)}\n"
            f"- Requires verification: {route.get('requires_verification', False)}"
        )
        augmented_task = resolved_task
        if context_str or session_str or ref_str or ui_hint or tone_str or memory_str:
            augmented_task = (
                f"{context_str}\n{session_str}\n{ref_str}\n{ui_hint}\n{memory_str}\n{router_directive}\n{tone_str}\nUSER REQUEST: {resolved_task}"
            )

        try:
            # Execute with augmented task
            result = super().run(augmented_task, *args, **kwargs)
            result = adjust_final_answer(result, self.memory, resolved_task)
            # Strict verifier pass
            result = self._verify_result(resolved_task, str(result))
            
            # 4. Log Result
            memory_client.log_event(session_id, "agent_result", str(result))
            # 4b. Store an episode summary (short)
            try:
                summary = f"User asked: {resolved_task} | Result: {str(result)[:120]}"
                memory_store.add_episode(session_id=session_id, summary=summary)
            except Exception:
                pass
            
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
