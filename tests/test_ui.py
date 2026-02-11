from core.ui import ui
import time

def test_ui():
    print("🧪 Testing Phase 4: UI Components...")
    
    try:
        # Test Welcome
        ui.print_welcome()
        time.sleep(0.5)
        
        # Test User Msg
        ui.print_user_msg("Hello Arka!")
        
        # Test Thought
        ui.print_thought("Processing request...")
        
        # Test Tool Call
        ui.print_tool_call("todo_add", "Buy milk")
        
        # Test Tool Result
        ui.print_tool_result("Added task: Buy milk")
        
        # Test Success
        ui.print_success("Final Answer: Task Complete.")
        
        print("\n✅ UI components rendered successfully (Visual check).")
        
    except Exception as e:
        print(f"❌ UI Verification Failed: {e}")

if __name__ == "__main__":
    test_ui()
