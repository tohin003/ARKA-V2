
from smolagents import tool
from tools.system import open_app, system_type, system_hotkey, system_press
from core.session_context import session_context
import time
import structlog
import re

logger = structlog.get_logger()


def _split_contacts(raw: str) -> list[str]:
    if not raw:
        return []
    # Split on common separators: comma, " and ", "&", ";"
    parts = re.split(r"\s*(?:,| and | & |;)\s*", raw.strip(), flags=re.IGNORECASE)
    cleaned = [p.strip() for p in parts if p.strip()]
    # If split didn't change, return original
    return cleaned if cleaned else [raw.strip()]


def _verify_chat_header(contact_name: str) -> bool:
    from tools.chrome_tools import chrome_get_text

    header_selectors = [
        "header span[title]",
        "header [data-testid='conversation-info-header-chat-title']",
        "header [role='button'] span[title]",
        "header h1, header h2, header h3",
    ]
    for sel in header_selectors:
        text = chrome_get_text(sel, max_length=2000)
        if contact_name.lower() in text.lower():
            return True
    return False

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

    # Respect explicit browser requests
    if session_context.last_task:
        lower = session_context.last_task.lower()
        if "browser" in lower or "whatsapp.com" in lower or "web" in lower:
            return "User requested WhatsApp in browser. Use send_whatsapp_web_message instead."
    
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


@tool
def send_whatsapp_web_message(contact_name: str, message: str) -> str:
    """
    Sends a WhatsApp message using WhatsApp Web (Chrome).

    Args:
        contact_name: The name of the contact.
        message: The text message to send.
    """
    from tools.chrome_tools import (
        chrome_wait_for_connection,
        chrome_navigate,
        chrome_wait_for_selector,
        chrome_click,
        chrome_type,
        chrome_press_key,
        chrome_verify_text,
    )

    # 1. Ensure Chrome bridge ready
    status = chrome_wait_for_connection()
    if "❌" in status:
        return status

    # 2. Navigate to WhatsApp Web
    nav = chrome_navigate("https://web.whatsapp.com")
    if "LOGIN REQUIRED" in nav:
        return (
            "WhatsApp Web requires login. Please scan the QR code in the Chrome tab, "
            "then run `chrome_continue()` and re-issue the request."
        )

    # 3. Wait for search box
    search_selectors = [
        "div[contenteditable='true'][data-tab='3']",
        "div[contenteditable='true'][role='textbox'][data-tab]",
        "div[contenteditable='true'][aria-label='Search input textbox']",
        "div[contenteditable='true'][aria-label='Search or start new chat']",
    ]
    search_selector = None
    for sel in search_selectors:
        res = chrome_wait_for_selector(sel, timeout_ms=15000)
        if res.startswith("✅") or "selector" in res or "ok" in res.lower():
            search_selector = sel
            break
    if not search_selector:
        return "Could not find WhatsApp Web search box. Ensure you are logged in."

    # 4. Split contacts if multiple
    contacts = _split_contacts(contact_name)
    if not contacts:
        return "No contacts provided."

    results = []
    for name in contacts:
        # Focus search box and search contact
        chrome_click(search_selector)
        chrome_type(name, selector=search_selector, clear=True)
        time.sleep(0.8)

        # Click first search result
        result_selectors = [
            "div[role='listitem']",
            "div[role='gridcell']",
            "div[aria-label][role='button']",
        ]
        clicked = False
        for sel in result_selectors:
            res = chrome_click(sel, index=0)
            if "❌" not in res:
                clicked = True
                break
        if not clicked:
            results.append(f"❌ Could not select '{name}'")
            continue

        # Optional verification of chat header
        if not _verify_chat_header(name):
            results.append(f"❌ Could not verify chat header for '{name}'")
            continue

        # Find composer and send message
        composer_selectors = [
            "div[contenteditable='true'][data-tab='10']",
            "div[contenteditable='true'][role='textbox'][data-tab='10']",
            "div[contenteditable='true'][role='textbox']",
        ]
        composer = None
        for sel in composer_selectors:
            res = chrome_wait_for_selector(sel, timeout_ms=10000)
            if res.startswith("✅") or "selector" in res or "ok" in res.lower():
                composer = sel
                break
        if not composer:
            results.append(f"❌ Could not find composer for '{name}'")
            continue

        chrome_click(composer)
        chrome_type(message, selector=composer, clear=True)
        chrome_press_key("Enter", selector=composer)

        verify = chrome_verify_text(message)
        if "❌" in verify:
            results.append(f"⚠️ Sent to '{name}' but not verified")
        else:
            results.append(f"✅ Sent to '{name}' (verified)")

        # Small pause before next contact
        time.sleep(0.6)

    session_context.update_app("WhatsApp Web")
    return "\n".join(results)
