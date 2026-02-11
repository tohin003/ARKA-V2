
from smolagents import tool
from tools.system import open_app, system_type, system_hotkey, system_press
import time
import structlog

logger = structlog.get_logger()

@tool
def send_whatsapp_message(contact_name: str, message: str) -> str:
    """
    Sends a WhatsApp message with Vision Verification and Robust Error Recovery.
    
    1. Search (Cmd+F)
    2. Vision Click (Verify result exists)
    3. Vision Verification (Verify chat opened)
    4. Send
    
    Args:
        contact_name: The name of the contact.
        message: The text message to send.
    """
    from tools.vision import get_screen_coordinates
    import pyautogui
    
    try:
        # 1. Open App
        open_app("WhatsApp")
        time.sleep(2) 
        
        # 2. Search for Contact
        # Reset Search State
        system_press("esc")
        time.sleep(0.2)
        
        system_hotkey(["command", "f"])
        time.sleep(0.5)
        
        # Robust Clear: Brute force backspace (safer than Cmd+A which can fail)
        pyautogui.press("backspace", presses=20, interval=0.02)
        time.sleep(0.2)
        
        # Type Name
        system_type(contact_name)
        time.sleep(1.5) 
        
        # 3. Hybrid Selection & Verification Loop
        max_retries = 2
        chat_verified = False
        
        # Initial Attempt: Vision Click (Relaxed prompt)
        # Check if "No results" is on screen? No, just look for contact.
        target_description = f"The contact row containing '{contact_name}' in the search list"
        coords = get_screen_coordinates(target_description)
        
        if "Error" not in coords:
            x, y = map(int, coords.split(","))
            pyautogui.moveTo(x, y, duration=0.3)
            pyautogui.click()
            time.sleep(1.0)
        else:
            # Fallback to key nav (starting at top)
            system_press("down")
            time.sleep(0.2)
            system_press("enter")
            time.sleep(0.8)

        # Verification Loop
        for attempt in range(max_retries):
            # Broader Verify: Look for name at the top
            verify_target = f"The name '{contact_name}' appearing in the top header area of the chat window"
            verify_coords = get_screen_coordinates(verify_target)
            
            if "Error" not in verify_coords:
                chat_verified = True
                break
            else:
                logger.warning("verify_failed", attempt=attempt, target=verify_target)
                print(f"DEBUG: Attempt {attempt+1} failed. Could not find '{contact_name}' in header. Repositioning...")
                
                # Retry strategy: Focus Search -> Down Arrow -> Enter
                system_hotkey(["command", "f"])
                time.sleep(0.5)
                
                # Move down based on attempt index
                clicks_needed = attempt + 2
                for _ in range(clicks_needed): 
                    system_press("down")
                    time.sleep(0.1)
                
                system_press("enter")
                time.sleep(1.0)
        
        if not chat_verified:
            # Final attempt: Just check if we see the name ANYWHERE in the right side?
            # Or ask user?
            return f"FAILED: Could not visually verify that the chat with '{contact_name}' is open. Messages NOT sent to maintain safety."

        # 5. Type & Send
        # Only reached if chat_verified is True
        
        # Ensure focus is on message bar (usually is, but good to ensure)
        # Clear Message Bar first (Cmd+A -> Backspace)
        system_hotkey(["command", "a"])
        time.sleep(0.1)
        system_press("backspace")
        time.sleep(0.1)
        
        system_type(message)
        time.sleep(0.5)
        system_press("enter")
        
        return f"Message sent to '{contact_name}' (Strictly Verified)."
        


    except Exception as e:
        return f"WhatsApp Error: {str(e)}"
