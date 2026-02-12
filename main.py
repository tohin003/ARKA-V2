#!/usr/bin/env python3
"""
main.py — ARKA V2 Entry Point

Run with:  python main.py
"""

import sys
import os
from dotenv import load_dotenv

# Ensure core modules are importable
sys.path.append(os.getcwd())

from core.engine import ArkaEngine
from core.ui import ui
from core.modes.planning import PlanningMode
from core.skills import skill_registry
from core.scheduler import heartbeat
from core.reflection import reflection_engine
from memory.db import memory_client
import structlog

# ─── Logging (File-only to keep UI clean) ─────────────────────────────
os.makedirs("logs", exist_ok=True)
structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=open("logs/arka.jsonl", "a")
    )
)
logger = structlog.get_logger()


def main():
    load_dotenv()

    # 1. Welcome Screen
    ui.print_welcome()

    # 2. Initialize Engine
    try:
        with ui.spinner("Initializing engine"):
            engine = ArkaEngine()
            planner = PlanningMode(engine)

        tool_count = len(engine.tools)
        ui.print_system(f"Engine ready — {tool_count} tools loaded")

        # Start Heartbeat
        heartbeat.start()
        ui.print_system("Heartbeat active")
        
        # Start Browser Bridge (Phase 7)
        from core.browser_bridge import browser_bridge
        browser_bridge.start()
        ui.print_system("Browser Bridge active (ws://localhost:7777)")
        
        ui.print_system("Ready for input")

        
    except Exception as e:
        ui.print_error(f"Failed to initialize: {e}")
        return

    # 3. Session tracking
    session_tasks = 0

    # 4. Main Loop
    while True:
        try:
            user_input = ui.get_input()

            if not user_input.strip():
                continue

            # Exit
            if user_input.lower() in ["exit", "quit", "q"]:
                heartbeat.stop()
                browser_bridge.stop()
                
                # Reflect on session if we did work
                if session_tasks > 0:
                    ui.print_system("Reflecting on session...")
                    try:
                        events = memory_client.get_session_history("latest", limit=20)
                        if events:
                            reflection_engine.reflect_on_events(events)
                    except Exception:
                        pass

                ui.print_goodbye()
                break

            # A. Slash Commands
            if user_input.startswith("/"):
                result = skill_registry.execute_skill(user_input)
                ui.print_tool_result(result)
                continue

            # B. Planning Mode
            if user_input.lower().startswith("plan ") or user_input.lower() == "plan":
                ui.print_thought("Entering planning mode")
                with ui.spinner("Planning"):
                    result = planner.start_plan(user_input)
                ui.print_success(result)
                session_tasks += 1
                continue

            # C. Execution Mode (Default)
            ui.print_thought("Processing")
            
            with ui.spinner("Thinking"):
                result = engine.run(user_input)

            ui.print_success(str(result))
            session_tasks += 1

        except KeyboardInterrupt:
            print()
            heartbeat.stop()
            ui.print_goodbye()
            sys.exit(0)
        except Exception as e:
            ui.print_error(str(e))
            logger.error("runtime_error", error=str(e))


if __name__ == "__main__":
    main()
