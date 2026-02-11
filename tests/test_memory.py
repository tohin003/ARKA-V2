from core.engine import ArkaEngine
from core.llm import model_router
from core.memory import MemoryManager
import time

def test_semantic_memory():
    print("🧠 Starting CORTEX Verification (Semantic Memory)...")
    
    # 1. Setup: Ensure clean slate or known state
    mem = MemoryManager()
    mem.append_fact("My favorite color is #ABCD12 (Test Color)")
    
    # 2. Initialize Engine (Should load the memory)
    print("   Initializing Engine (injecting memory)...")
    # model is now handled internally or passed via tools, but let's check init signature
    # ArkaEngine init signature is def __init__(self, tools=None, additional_imports=None):
    agent = ArkaEngine()
    
    # 3. Test Retrieval via LLM
    print("   Asking Agent about the secret color...")
    response = agent.run("What is my favorite color? Reply with just the hex code.")
    print(f"   Agent Response: {response}")
    
    if "#ABCD12" in str(response):
        print("✅ SUCCESS: Agent recalled the fact from Semantic Memory!")
    else:
        print(f"❌ FAILURE: Agent did not recall the correct color. Got: {response}")
        exit(1)

    # 4. Test Memory Update (Tool Usage)
    print("\n   Testing 'remember_fact' tool usage...")
    task = "I also like the color blue. Please remember that factor."
    agent.run(task)
    
    # 5. Verify Tool Execution by reading file
    with open("memory/user_profile.md", "r") as f:
        content = f.read()
        if "color blue" in content:
            print("✅ SUCCESS: 'remember_fact' tool successfully updated user_profile.md")
        else:
            print("❌ FAILURE: Profile was not updated with 'color blue'.")
            exit(1)

if __name__ == "__main__":
    test_semantic_memory()
