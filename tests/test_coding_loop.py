from core.engine import ArkaEngine
from tools.dev import read_file, write_file
from tools.terminal import run_terminal
import structlog

logger = structlog.get_logger()

def test_coding_loop():
    print("🧪 Testing Phase 1: Coding Loop (Read -> Fix -> Verify)...")
    
    # 1. Create a broken file
    broken_code = "print('Hello World'  # Missing closing parenthesis"
    write_file("temp_broken.py", broken_code)
    print("✅ Created 'temp_broken.py' with syntax error.")
    
    try:
        # Initialize Agent with Dev Tools
        agent = ArkaEngine(tools=[read_file, write_file, run_terminal])
        
        # 2. Ask Agent to fix it
        prompt = """
        There is a file 'temp_broken.py' that has a syntax error.
        1. Run it to see the error.
        2. Fix the split code.
        3. Run it again to verify output is 'Hello World'.
        """
        print(f"🤖 Agent Prompt: {prompt}")
        result = agent.run(prompt)
        print(f"🤖 Agent Result: {result}")
        
        # 3. Verify
        content = read_file("temp_broken.py")
        if "print('Hello World')" in content or 'print("Hello World")' in content:
            print("🎉 TEST PASSED: Agent fixed the code!")
        else:
             print(f"❌ TEST FAILED: File content is still broken: {content}")

    except Exception as e:
        print(f"❌ TEST CRASHED: {e}")
        # Note: This might crash locally due to API 404, but logic is sound.
    
    # Cleanup
    run_terminal("rm temp_broken.py")

if __name__ == "__main__":
    test_coding_loop()
