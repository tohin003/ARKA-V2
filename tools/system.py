from smolagents import tool
from tools.vision import get_screen_coordinates
import pyautogui
import subprocess
import structlog
import time

logger = structlog.get_logger()

# Safety Pre-check
pyautogui.FAILSAFE = True

@tool
def system_click(element_description: str) -> str:
    """
    Visually finds an element on the screen and clicks it.
    
    Args:
        element_description: Description of the UI element to click (e.g. "Send button").
    """
    try:
        # 1. Get Coordinates via Vision
        logger.info("system_click_start", target=element_description)
        coords_str = get_screen_coordinates(element_description)
        
        if "Error" in coords_str:
            return coords_str
        
        x, y = map(int, coords_str.split(","))
        
        # 2. Click
        # Move smooth to look natural and give user time to abort (Move mouse to corner)
        pyautogui.moveTo(x, y, duration=0.5) 
        pyautogui.click()
        
        return f"Clicked on {element_description} at ({x}, {y})"
    except Exception as e:
        return f"Click Error: {str(e)}"

@tool
def system_type(text: str) -> str:
    """
    Types text into the currently focused field.
    
    Args:
        text: The text to type.
    """
    try:
        pyautogui.write(text, interval=0.05) # Slower typing to prevent skipped keys
        return f"Typed: {text}"
    except Exception as e:
        return f"Type Error: {str(e)}"

@tool
def open_app(app_name: str, url: str = None) -> str:
    """
    Opens an application, or a URL in a specific application.
    
    Args:
        app_name: The name of the application (e.g. "Safari", "Spotify"). 
                  If app is unknown, tries to open roughly matching app.
        url: Optional URL to open in the app.
    """
    try:
        cmd = ["open", "-a", app_name]
        if url:
            cmd.append(url)
            
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        time.sleep(2)
        
        # Verify app is actually running
        # Fuzzy match: try pgrep -f first check exact, then loosen
        verify = subprocess.run(["pgrep", "-f", app_name], capture_output=True)
        if verify.returncode != 0:
            # Try simpler name (e.g. "Apple Music" -> "Music")
            simple_name = app_name.replace("Apple ", "").replace("Google ", "").strip()
            verify_simple = subprocess.run(["pgrep", "-f", simple_name], capture_output=True)
            if verify_simple.returncode != 0:
                return f"Error: Command sent, but '{app_name}' process not found running."
            
        return f"Opened {app_name} " + (f"with {url}" if url else "")
    except subprocess.CalledProcessError as e:
        # Fallback: If app not found and we have a URL, just open URL (default browser)
        if url and "Unable to find application" in e.stderr:
            try:
                subprocess.run(["open", url], check=True)
                return f"Could not find '{app_name}', but opened {url} in default browser."
            except Exception as e2:
                return f"Error: {str(e2)}"
                
        return f"Open App Error: {e.stderr or str(e)}"
    except Exception as e:
        return f"System Error: {str(e)}"

@tool
def system_hotkey(keys: list[str]) -> str:
    """
    Presses a combination of keys (e.g. ["command", "f"]).
    
    Args:
        keys: List of keys to press together.
    """
    try:
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey: {'+'.join(keys)}"
    except Exception as e:
        return f"Hotkey Error: {str(e)}"

@tool
def system_press(key: str) -> str:
    """
    Presses a single key (e.g. "enter", "esc", "tab").
    
    Args:
        key: The key to press.
    """
    try:
        pyautogui.press(key)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Key Error: {str(e)}"
