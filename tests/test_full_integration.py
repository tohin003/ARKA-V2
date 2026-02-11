"""
tests/test_full_integration.py — Comprehensive ARKA V2 Integration Test

This is a FULL SYSTEMS CHECK. It tests every subsystem end-to-end
and cross-verifies that the agent's claimed results are actually correct.

Subsystems tested:
  1. Engine Initialization (all 19 tools load)
  2. Semantic Memory (read, write, persist)
  3. MistakeGuard (safety blocks)
  4. SQLite Session DB (log + retrieve)
  5. Skill Registry (slash commands)
  6. Heartbeat Scheduler (start, pulse, stop)
  7. MCP Bridge (connect, list, call, disconnect)
  8. LLM Execution: Simple task with cross-verification
  9. LLM Execution: Memory recall with cross-verification
  10. LLM Execution: Tool usage (todo) with cross-verification
"""

import sys, os, time, json, datetime
sys.path.insert(0, os.getcwd())

# ─── Color helpers ────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

results = {}

def log_test(name, passed, detail=""):
    results[name] = passed
    icon = f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))

def section(title):
    print(f"\n{BLUE}{'─'*60}{RESET}")
    print(f"{BLUE}  {title}{RESET}")
    print(f"{BLUE}{'─'*60}{RESET}")


def run_all_tests():
    # ══════════════════════════════════════════════════════════════════
    # 1. ENGINE INITIALIZATION
    # ══════════════════════════════════════════════════════════════════
    section("1. ENGINE INITIALIZATION")
    try:
        from core.engine import ArkaEngine
        engine = ArkaEngine()
        tool_names = [t.name for t in engine.tools.values()] if hasattr(engine, 'tools') else []
        tool_count = len(tool_names)
        log_test("Engine init", True, f"{tool_count} tools loaded")
        
        # Cross-verify: check specific tools exist
        expected_tools = ["music_control", "remember_fact", "list_mcp_tools", "call_mcp_tool", 
                          "web_search", "visit_page", "todo_add", "system_click"]
        missing = [t for t in expected_tools if t not in tool_names]
        log_test("Critical tools present", len(missing) == 0, 
                 f"Missing: {missing}" if missing else f"All {len(expected_tools)} critical tools found")
    except Exception as e:
        log_test("Engine init", False, str(e))
        print(f"{RED}FATAL: Engine failed to initialize. Aborting remaining tests.{RESET}")
        return

    # ══════════════════════════════════════════════════════════════════
    # 2. SEMANTIC MEMORY
    # ══════════════════════════════════════════════════════════════════
    section("2. SEMANTIC MEMORY")
    try:
        from core.memory import MemoryManager
        mem = MemoryManager()
        
        # Read profile
        profile = mem.get_profile()
        log_test("Memory read", len(profile) > 0, f"{len(profile)} chars loaded")
        
        # Append a test fact
        marker = f"IntegTest-{int(time.time())}"
        result = mem.append_fact(f"Test marker: {marker}")
        log_test("Memory append", marker in result, result.strip())
        
        # Cross-verify: re-read and check marker exists
        profile_after = mem.get_profile()
        log_test("Memory persistence", marker in profile_after, "Marker found in re-read")
        
        # Clean up: remove our test line
        with open(mem.profile_path, "r") as f:
            lines = f.readlines()
        with open(mem.profile_path, "w") as f:
            for line in lines:
                if marker not in line:
                    f.write(line)
    except Exception as e:
        log_test("Memory system", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 3. MISTAKEGUARD (Safety)
    # ══════════════════════════════════════════════════════════════════
    section("3. MISTAKEGUARD (Safety)")
    try:
        from memory.mistakes import mistake_guard
        
        # Should block dangerous commands
        blocked = mistake_guard.validate_command("rm -rf /")
        log_test("Block rm -rf /", blocked is not None, blocked)
        
        blocked2 = mistake_guard.validate_command("sudo apt install something")
        log_test("Block sudo", blocked2 is not None, blocked2)
        
        # Should allow safe commands
        safe = mistake_guard.validate_command("ls -la")
        log_test("Allow safe cmd", safe is None, "No block on 'ls -la'")
        
        # Lazy code detection
        lazy = mistake_guard.validate_code("def foo():\n    # ... rest of code\n    pass")
        log_test("Detect lazy code", lazy is not None, lazy)
        
        good_code = mistake_guard.validate_code("def foo():\n    return 42")
        log_test("Allow good code", good_code is None, "No warning")
    except Exception as e:
        log_test("MistakeGuard", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 4. SQLITE SESSION DB
    # ══════════════════════════════════════════════════════════════════
    section("4. SQLITE SESSION DB")
    try:
        from memory.db import memory_client
        import uuid
        
        test_session = f"test-{uuid.uuid4()}"
        memory_client.log_event(test_session, "test_event", "Integration test entry")
        
        # Cross-verify: retrieve the event
        history = memory_client.get_session_history(test_session)
        log_test("DB log + retrieve", len(history) > 0 and history[0]["content"] == "Integration test entry",
                 f"Retrieved {len(history)} event(s)")
    except Exception as e:
        log_test("Session DB", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 5. SKILL REGISTRY
    # ══════════════════════════════════════════════════════════════════
    section("5. SKILL REGISTRY")
    try:
        from core.skills import skill_registry
        
        # /help should list skills
        help_result = skill_registry.execute_skill("/help")
        log_test("/help command", "/commit" in help_result and "/status" in help_result, help_result)
        
        # Unknown skill
        unknown = skill_registry.execute_skill("/nonexistent")
        log_test("Unknown skill handling", "Unknown skill" in unknown, unknown)
    except Exception as e:
        log_test("Skill Registry", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 6. HEARTBEAT SCHEDULER
    # ══════════════════════════════════════════════════════════════════
    section("6. HEARTBEAT SCHEDULER")
    try:
        import schedule as schedule_lib
        from core.scheduler import HeartbeatScheduler
        
        hb = HeartbeatScheduler()
        schedule_lib.clear()
        schedule_lib.every(1).seconds.do(hb._pulse)
        hb._jobs_registered = 1
        
        import threading
        hb._stop_event.clear()
        hb._thread = threading.Thread(target=hb._run_loop, name="Test-HB", daemon=True)
        hb._thread.start()
        
        log_test("Heartbeat start", hb.is_alive, "Thread alive")
        
        time.sleep(2)
        log_test("Heartbeat pulse", hb._pulse_count > 0, f"Pulse count: {hb._pulse_count}")
        
        hb.stop()
        time.sleep(0.5)
        log_test("Heartbeat stop", not hb.is_alive, "Thread stopped")
    except Exception as e:
        log_test("Heartbeat", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 7. MCP BRIDGE
    # ══════════════════════════════════════════════════════════════════
    section("7. MCP BRIDGE")
    try:
        from core.mcp_client import MCPBridge
        
        test_dir = os.path.realpath("/tmp/arka_integ_test")
        os.makedirs(test_dir, exist_ok=True)
        with open(os.path.join(test_dir, "probe.txt"), "w") as f:
            f.write("MCP-PROBE-OK")
        
        bridge = MCPBridge()
        bridge.connect("fs-test", "npx", ["-y", "@modelcontextprotocol/server-filesystem", test_dir])
        
        tools = bridge.list_tools()
        log_test("MCP connect + list", len(tools) > 0, f"{len(tools)} tools from fs-test")
        
        content = bridge.call_tool("read_file", {"path": os.path.join(test_dir, "probe.txt")})
        log_test("MCP call_tool (cross-verify)", "MCP-PROBE-OK" in content, f"Got: {content[:40]}")
        
        bridge.disconnect_all()
        log_test("MCP disconnect", not bridge.status["running"], "Clean shutdown")
        
        # Cleanup
        os.remove(os.path.join(test_dir, "probe.txt"))
        os.rmdir(test_dir)
    except Exception as e:
        log_test("MCP Bridge", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 8. LLM EXECUTION: Simple Math (Cross-Verify)
    # ══════════════════════════════════════════════════════════════════
    section("8. LLM EXECUTION: Simple Task")
    try:
        result = engine.run("What is 137 * 29? Reply with ONLY the number, nothing else.")
        # Cross-verify: 137 * 29 = 3973
        correct = "3973" in str(result)
        log_test("LLM math (cross-verify)", correct, f"Agent said: {result}, expected: 3973")
    except Exception as e:
        log_test("LLM simple task", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 9. LLM EXECUTION: Memory Recall (Cross-Verify)
    # ══════════════════════════════════════════════════════════════════
    section("9. LLM EXECUTION: Memory Recall")
    try:
        # Add a known fact first
        mem.append_fact("The user's favorite number is 7734.")
        
        # Re-init engine to pick up the new fact
        engine2 = ArkaEngine()
        result2 = engine2.run("What is my favorite number? Reply with ONLY the number.")
        
        # Cross-verify
        correct2 = "7734" in str(result2)
        log_test("LLM memory recall (cross-verify)", correct2, f"Agent said: {result2}, expected: 7734")
        
        # Cleanup
        with open(mem.profile_path, "r") as f:
            lines = f.readlines()
        with open(mem.profile_path, "w") as f:
            for line in lines:
                if "7734" not in line:
                    f.write(line)
    except Exception as e:
        log_test("LLM memory recall", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 10. LLM EXECUTION: Tool Usage - TODO (Cross-Verify)
    # ══════════════════════════════════════════════════════════════════
    section("10. LLM EXECUTION: Tool Usage (todo_add)")
    try:
        result3 = engine.run("Add a todo item: 'Fix integration test bugs'. Reply with the confirmation.")
        
        # Cross-verify by checking the todo list directly
        # The TodoManager saves to disk, so reload from file for true cross-verification
        from tools.todo import manager as todo_manager
        todo_manager._load()  # reload from disk
        all_todos = todo_manager.todos  # correct attribute name
        found = any("Fix integration test bugs" in t.get("task", "") for t in all_todos)
        log_test("LLM tool use (cross-verify)", found, 
                 f"Agent said: {str(result3)[:80]}... | Todo list has {len(all_todos)} items, target found: {found}")
    except Exception as e:
        log_test("LLM tool use", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════
    section("FINAL REPORT")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, ok in results.items():
        icon = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
        print(f"  {icon} {name}")
    
    print(f"\n{BLUE}{'═'*60}{RESET}")
    if passed == total:
        print(f"  {GREEN}🎉 ALL {total}/{total} TESTS PASSED!{RESET}")
    else:
        failed = total - passed
        print(f"  {YELLOW}⚠️  {passed}/{total} PASSED, {failed} FAILED{RESET}")
    print(f"{BLUE}{'═'*60}{RESET}")
    
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
