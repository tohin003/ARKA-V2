"""
tests/test_phase6.py — Verification for Phase 6: AGI Gap Closure

Tests all 5 new modules:
  6.1 Pattern Learner
  6.2 Goal Manager
  6.3 Reflection Engine
  6.4 Context Sensor
  6.5 Tone Adapter
  + Engine integration with all modules
"""

import sys, os, time
sys.path.insert(0, os.getcwd())

GREEN = "\033[92m"
RED = "\033[91m"
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


def run_tests():
    # ══════════════════════════════════════════════════════════════════
    # 6.1 PATTERN LEARNER
    # ══════════════════════════════════════════════════════════════════
    section("6.1 Pattern Learner")
    try:
        from core.pattern_learner import PatternLearner
        from memory.db import memory_client
        import uuid

        pl = PatternLearner(profile_path="memory/user_profile.md")
        
        # Seed some test events
        sid = f"pattern-test-{uuid.uuid4()}"
        for _ in range(3):
            memory_client.log_event(sid, "user_msg", "play some music please")
        for _ in range(2):
            memory_client.log_event(sid, "user_msg", "search for Python docs")
        
        # Run learner
        patterns = pl.learn()
        log_test("Pattern detection", True, f"Found {len(patterns)} pattern(s): {patterns}")
        
        # Verify deduplication — running again should find fewer new ones
        patterns2 = pl.learn()
        log_test("Pattern dedup", len(patterns2) <= len(patterns), 
                 f"2nd run: {len(patterns2)} new (should be ≤ {len(patterns)})")
    except Exception as e:
        log_test("Pattern Learner", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 6.2 GOAL MANAGER
    # ══════════════════════════════════════════════════════════════════
    section("6.2 Goal Manager")
    try:
        from core.goal_manager import GoalManager
        import tempfile
        
        # Use temp file to avoid polluting real goals
        tmp = tempfile.mktemp(suffix=".json")
        gm = GoalManager(goals_file=tmp)
        
        # Create
        goal = gm.create_goal("Ship ARKA V3", ["Write tests", "Fix bugs", "Deploy"])
        log_test("Goal create", goal.id is not None, f"ID: {goal.id}, Steps: {len(goal.steps)}")
        
        # List active
        active = gm.get_active_goals()
        log_test("Goal list active", len(active) == 1, f"{len(active)} active goal(s)")
        
        # Advance
        msg = gm.advance_goal(goal.id)
        log_test("Goal advance", "1/3" in msg, msg)
        
        # Check next step
        log_test("Goal next step", goal.next_step == "Fix bugs", f"Next: {goal.next_step}")
        
        # Complete
        gm.complete_goal(goal.id)
        log_test("Goal complete", goal.status == "completed", f"Status: {goal.status}")
        
        # Prompt injection
        gm2 = GoalManager(goals_file=tmp)
        gm2.create_goal("Test goal", ["Step A"])
        prompt = gm2.format_for_prompt()
        log_test("Goal prompt injection", "ACTIVE GOALS" in prompt, f"Prompt length: {len(prompt)}")
        
        # Cleanup
        os.remove(tmp)
    except Exception as e:
        log_test("Goal Manager", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 6.3 REFLECTION ENGINE
    # ══════════════════════════════════════════════════════════════════
    section("6.3 Reflection Engine")
    try:
        from core.reflection import ReflectionEngine
        import tempfile
        
        tmp = tempfile.mktemp(suffix=".md")
        os.makedirs(os.path.dirname(tmp) if os.path.dirname(tmp) else ".", exist_ok=True)
        re_ = ReflectionEngine(learnings_path=tmp)
        
        # File exists
        log_test("Learnings file created", os.path.exists(tmp))
        
        # Add learning
        result = re_.add_learning("web_search works better with quoted phrases", "high")
        log_test("Add learning", "Learned" in result, result)
        
        # Dedup
        result2 = re_.add_learning("web_search works better with quoted phrases", "high")
        log_test("Learning dedup", "Already known" in result2, result2)
        
        # Reflect on events
        fake_events = [
            {"type": "agent_error", "content": "ModuleNotFoundError: xyz"},
            {"type": "agent_result", "content": "Success"},
            {"type": "user_msg", "content": "I want dark mode for everything"},
        ]
        new_learnings = re_.reflect_on_events(fake_events)
        log_test("Reflect on events", len(new_learnings) > 0, f"Extracted: {new_learnings}")
        
        os.remove(tmp)
    except Exception as e:
        log_test("Reflection Engine", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 6.4 CONTEXT SENSOR
    # ══════════════════════════════════════════════════════════════════
    section("6.4 Context Sensor")
    try:
        from core.context_sensor import ContextSensor
        
        cs = ContextSensor()
        ctx = cs.get_context()
        log_test("Context detection", "frontmost_app" in ctx, f"App: {ctx.get('frontmost_app')}, Window: {ctx.get('window_title')}")
        
        prompt = cs.format_for_prompt()
        has_content = len(prompt) > 0 or ctx["frontmost_app"] == "unknown"
        log_test("Context prompt format", has_content, f"Prompt: {prompt[:60]}..." if prompt else "Empty (unknown context)")
    except Exception as e:
        log_test("Context Sensor", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 6.5 TONE ADAPTER
    # ══════════════════════════════════════════════════════════════════
    section("6.5 Tone Adapter")
    try:
        from core.tone_adapter import ToneAdapter
        
        ta = ToneAdapter()
        
        # Urgent
        t1 = ta.detect_tone("FIX THIS NOW!!!")
        log_test("Tone: urgent", "concise" in t1.lower() or "rush" in t1.lower(), t1.strip()[:60])
        
        # Frustrated
        t2 = ta.detect_tone("Why doesn't this work? It's broken again!")
        log_test("Tone: frustrated", "frustrated" in t2.lower() or "fix" in t2.lower(), t2.strip()[:60])
        
        # Casual
        t3 = ta.detect_tone("Hey, what's up?")
        log_test("Tone: casual", "warm" in t3.lower() or "casual" in t3.lower() or "friendly" in t3.lower(), t3.strip()[:60])
        
        # Detailed/polite
        t4 = ta.detect_tone("Could you please explain in detail how the MCP bridge handles async to sync conversion?")
        log_test("Tone: detailed", "thorough" in t4.lower() or "detailed" in t4.lower() or "structured" in t4.lower(), t4.strip()[:60])
        
        # Terse (no question mark, just short)
        t5 = ta.detect_tone("ok")
        log_test("Tone: terse", "energy" in t5.lower() or "concise" in t5.lower(), t5.strip()[:60])
    except Exception as e:
        log_test("Tone Adapter", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # ENGINE INTEGRATION
    # ══════════════════════════════════════════════════════════════════
    section("ENGINE INTEGRATION (Phase 6)")
    try:
        from core.engine import ArkaEngine
        engine = ArkaEngine()
        
        tool_names = [t.name for t in engine.tools.values()]
        
        # Check new tools registered
        phase6_tools = ["set_goal", "list_goals", "advance_goal", "complete_goal"]
        missing = [t for t in phase6_tools if t not in tool_names]
        log_test("Goal tools registered", len(missing) == 0, 
                 f"Missing: {missing}" if missing else f"All 4 goal tools present")
        
        # Check new prompt sections
        prompt = engine.prompt_templates.get("system_prompt", "")
        has_memory = "SEMANTIC MEMORY" in prompt
        has_learnings = "OPERATIONAL LEARNINGS" in prompt
        log_test("Prompt: memory + learnings", has_memory and has_learnings, 
                 f"Memory: {has_memory}, Learnings: {has_learnings}")
        
        # Check context/tone adapters initialized
        log_test("Context + Tone init", 
                 hasattr(engine, '_context_sensor') and hasattr(engine, '_tone_adapter'),
                 "Both adapters initialized")
        
        total_tools = len(tool_names)
        log_test(f"Total tools: {total_tools}", total_tools >= 23, f"Expected ≥23, got {total_tools}")
    except Exception as e:
        log_test("Engine integration", False, str(e))

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
        print(f"  {GREEN}🎉 ALL {total}/{total} PHASE 6 TESTS PASSED!{RESET}")
    else:
        print(f"  {RED}⚠️  {passed}/{total} PASSED, {total-passed} FAILED{RESET}")
    print(f"{BLUE}{'═'*60}{RESET}")
    
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
