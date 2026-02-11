from core.engine import ArkaEngine
from core.modes.planning import PlanningMode
from tools.dev import read_file
import os

def test_planning_mode():
    print("🧪 Testing Phase 3: Planning Mode...")
    
    # Setup
    engine = ArkaEngine()
    planner = PlanningMode(engine)
    
    # Clean previous plan
    if os.path.exists("implementation_plan.md"):
        os.remove("implementation_plan.md")
        
    try:
        # Request
        request = "Create a python script that calculates the Fibonacci sequence."
        print(f"📝 Request: {request}")
        
        result = planner.start_plan(request)
        print(f"🤖 Result: {result}")
        
        # Verify File
        if os.path.exists("implementation_plan.md"):
            content = read_file("implementation_plan.md")
            print("\n📄 Generated Plan Content (First 500 chars):")
            print(content[:500])
            
            if "Fibonacci" in content and "Goal" in content:
                 print("✅ Plan generated successfully with relevant content.")
            else:
                 print("⚠️ Plan generated but content seems off.")
        else:
             print("❌ Plan file not created.")
             
    except Exception as e:
        print(f"❌ Planning Failed: {e}")

if __name__ == "__main__":
    test_planning_mode()
