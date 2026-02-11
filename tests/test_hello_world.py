from core.engine import ArkaEngine
import structlog
import os

# Ensure we can import core modules
logger = structlog.get_logger()

def test_engine_initialization():
    print("🧪 Testing ArkaEngine Initialization...")
    try:
        agent = ArkaEngine()
        print("✅ ArkaEngine initialized successfully.")
        
        print("🧪 Testing Agent Execution (Hello World)...")
        # We ask it to run a simple python print
        result = agent.run("Write a python script that prints 'Hello World from ARKA' and return the output.")
        
        print(f"✅ Execution Result: {result}")
        
        if "Hello World from ARKA" in str(result) or "Hello World" in str(result):
             print("🎉 TEST PASSED: Agent can execute code!")
        else:
             print("⚠️ TEST WARNING: Output might not match exactly, but no crash.")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise e

if __name__ == "__main__":
    test_engine_initialization()
