from core.engine import ArkaEngine
from tools.terminal import run_terminal
import structlog
import time

logger = structlog.get_logger()

def test_god_mode():
    print("🧪 Testing Phase 2: God Mode (Hardware & System Control)...")
    
    try:
        # Initialize Agent (Tools are auto-loaded in __init__ now)
        agent = ArkaEngine()
        
        # 1. Test Hardware (Safe)
        prompt_hardware = """
        I want to test your hardware controls.
        1. Turn system volume to 14.
        2. Check if WiFi is on.
        3. Open the 'Calculator' app.
        """
        print(f"🤖 Agent Prompt: {prompt_hardware}")
        result = agent.run(prompt_hardware)
        print(f"🤖 Agent Result: {result}")
        
        # 2. Verify Volume (using terminal)
        vol_check = run_terminal("osascript -e 'output volume of (get volume settings)'")
        if "14" in vol_check:
             print("🎉 TEST PASSED: Volume set correctly!")
        else:
             print(f"⚠️ TEST WARNING: Volume might be different: {vol_check}")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")

if __name__ == "__main__":
    test_god_mode()
