from core.engine import ArkaEngine
from core.memory import MemoryManager
import time
import sys

def colored_print(msg, color="white"):
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{msg}{colors['reset']}")

def test_robust_memory():
    colored_print("\n🧠 STARTING ROBUST CORTEX VERIFICATION", "blue")
    
    # --- PHASE 1: INJECTION ---
    colored_print("\n[Phase 1] Teaching ARKA new facts...", "yellow")
    agent_1 = ArkaEngine()
    
    # Fact 1: A Secret
    task1 = "My secret code is 'OMEGA-99'. Please remember this securely."
    print(f"User: {task1}")
    agent_1.run(task1)
    
    # Fact 2: A Preference
    task2 = "I prefer to be addressed as 'Commander' from now on. Remember that."
    print(f"User: {task2}")
    agent_1.run(task2)
    
    time.sleep(1) # Ensure file write flush
    
    # --- PHASE 2: PERSISTENCE (New Session) ---
    colored_print("\n[Phase 2] Simulating Restart (New Session)...", "yellow")
    agent_2 = ArkaEngine()
    
    # Test 1: Recall Secret
    q1 = "What is my secret code? Reply with just the code."
    print(f"User: {q1}")
    res1 = agent_2.run(q1)
    colored_print(f"Agent: {res1}", "white")
    
    if "OMEGA-99" in str(res1):
        colored_print("✅ SUCCESS: Remembered Secret Code", "green")
    else:
        colored_print("❌ FAILURE: Forgot Secret Code", "red")
        
    # Test 2: Recall Preference
    q2 = "Who am I?"
    print(f"User: {q2}")
    res2 = agent_2.run(q2)
    colored_print(f"Agent: {res2}", "white")
    
    if "Commander" in str(res2):
        colored_print("✅ SUCCESS: Remembered to call user 'Commander'", "green")
    else:
        colored_print("❌ FAILURE: Forgot User's Title", "red")

    # --- PHASE 3: UPDATE (Conflict Resolution) ---
    colored_print("\n[Phase 3] Testing Memory Update...", "yellow")
    
    # Update Fact 1
    task3 = "Actually, I changed my secret code to 'ALPHA-00'. Forget the old one, remember this new one."
    print(f"User: {task3}")
    agent_2.run(task3)
    
    time.sleep(1)
    
    # Restart again
    agent_3 = ArkaEngine()
    q3 = "What is my CURRENT secret code?"
    print(f"User: {q3}")
    res3 = agent_3.run(q3)
    colored_print(f"Agent: {res3}", "white")
    
    if "ALPHA-00" in str(res3):
         colored_print("✅ SUCCESS: Updated Secret Code", "green")
    else:
         colored_print("⚠️ WARNING: Might be using old code or confused.", "red")

if __name__ == "__main__":
    test_robust_memory()
