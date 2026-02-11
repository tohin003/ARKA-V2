from smolagents import tool
from core.vision_client import vision_client
import subprocess
import os
import time

SCREENSHOT_PATH = "/tmp/arka_vision_screenshot.jpg"

@tool
def get_screen_coordinates(description: str) -> str:
    """
    Takes a screenshot and finds the X,Y coordinates of a UI element described by text.
    Use this before clicking.
    
    Args:
        description: Text description of what to find (e.g. "The Play button", "Chrome Icon").
    """
    # 1. Capture Screenshot
    # We use 'screencapture' (native macOS) as it's faster than pyautogui for full screen
    # -x: no sound, -t jpg: format
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)
        
    cmd = f"screencapture -x -t jpg {SCREENSHOT_PATH}"
    subprocess.run(cmd, shell=True, check=True)
    
    # 2. Ask Vision Client
    try:
        x, y = vision_client.get_coordinates(SCREENSHOT_PATH, description)
        return f"{x},{y}"
    except Exception as e:
        return f"Error locating element: {str(e)}"
