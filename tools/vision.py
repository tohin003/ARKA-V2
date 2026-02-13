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


@tool
def find_text_on_screen(query: str, region_hint: str = "top section") -> str:
    """
    Takes a screenshot and finds text matching the query, optionally focusing on a region.

    Args:
        query: The text to find (e.g. song name).
        region_hint: A hint like "top section", "left side", or "full screen".
    """
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)

    cmd = f"screencapture -x -t jpg {SCREENSHOT_PATH}"
    subprocess.run(cmd, shell=True, check=True)

    try:
        result = vision_client.find_text(SCREENSHOT_PATH, query, region_hint=region_hint)
        if not result.get("found"):
            return "NOT_FOUND"
        text = result.get("text", "")
        x = result.get("x")
        y = result.get("y")
        if x is not None and y is not None:
            return f"FOUND: {text} at {x},{y}"
        return f"FOUND: {text}"
    except Exception as e:
        return f"Error finding text: {str(e)}"


@tool
def find_and_click_text_on_screen(query: str, region_hint: str = "top section") -> str:
    """
    Finds matching text on screen and clicks it.

    Args:
        query: The text to find (e.g. song name).
        region_hint: A hint like "top section", "left side", or "full screen".
    """
    if os.path.exists(SCREENSHOT_PATH):
        os.remove(SCREENSHOT_PATH)

    cmd = f"screencapture -x -t jpg {SCREENSHOT_PATH}"
    subprocess.run(cmd, shell=True, check=True)

    try:
        from tools.system import system_click_at
        result = vision_client.find_text(SCREENSHOT_PATH, query, region_hint=region_hint)
        if not result.get("found"):
            return "NOT_FOUND"
        x = result.get("x")
        y = result.get("y")
        if x is None or y is None:
            return "FOUND_BUT_NO_COORDS"
        click_res = system_click_at(int(x), int(y))
        return f"CLICKED: {result.get('text', query)} at {x},{y} | {click_res}"
    except Exception as e:
        return f"Error finding/clicking text: {str(e)}"
