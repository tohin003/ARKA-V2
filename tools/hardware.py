from smolagents import tool
import subprocess
import structlog

import structlog
from tools.vision import get_screen_coordinates
import pyautogui
import time

logger = structlog.get_logger()

@tool
def music_control(action: str, song_name: str = None) -> str:
    """
    Control Apple Music. Can play specific songs.
    
    Args:
        action: 'play', 'pause', 'next', 'prev'.
        song_name: The EXACT title of the song to play.
                   IMPORTANT: Treat this as a LITERAL song title. 
                   Do not pick a random song based on the input as a mood/genre.
                   Example: If input is "play breakup party", song_name MUST be "Breakup Party".
    """
    cmd_map = {
        'play': 'play',
        'pause': 'pause',
        'next': 'next track',
        'prev': 'previous track'
    }
    if action not in cmd_map:
        return f"Invalid action. Use: {list(cmd_map.keys())}"
    
    try:
        if action == 'play' and song_name:
            # AppleScript to play specific track
            # AppleScript to play specific track (Search in Library)
            # Helper for attempting playback
            def try_play(query):
                script = f'''
                tell application "Music"
                    try
                        play (first track of playlist "Library" whose name contains "{query}")
                        return "Success"
                    on error
                        return "Song not found"
                    end try
                end tell
                '''
                res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
                output = res.stdout.strip()
                return "Song not found" not in output, output, res.stderr

            # 1. Try exact match (e.g. "Punkrocker" or "Navior song")
            found, out, err = try_play(song_name)
            if found:
                return f"Playing song: {song_name}"
            
            # 2. Try stripping " song" suffix (e.g. "Navior song" -> "Navior")
            # Clean song name if users say "Navior song" or "2 khatole song"
            search_name = song_name
            if search_name.lower().endswith(" song"):
                search_name = search_name[:-5].strip()

            # 3. Fallback: Try playing via Global Search URL (V1-style)
            try:
                search_script = f'open location "music://music.apple.com/search?term={search_name}"'
                subprocess.run(["osascript", "-e", search_script], check=True)
                
                # Visual Verification & Click (God Mode)
                time.sleep(4) 
                
                try:
                    # Strategy A: Play Button (Triangle)
                    target_desc = f"The play button (triangle icon) overlaid on the artwork for the song '{search_name}'"
                    coords = get_screen_coordinates(target_desc)
                    
                    if "Error" not in coords:
                        x, y = map(int, coords.split(","))
                        pyautogui.moveTo(x, y, duration=0.5)
                        pyautogui.click()
                        return f"Playing song '{search_name}' (Global Search via Vision Click)."
                    
                    # Strategy B: Double Click the Artwork (if play button hidden)
                    logger.warning("vision_fallback_retry", reason="play_button_not_found", target=target_desc)
                    target_desc_b = f"The album artwork for the song '{search_name}'"
                    coords_b = get_screen_coordinates(target_desc_b)
                    
                    if "Error" not in coords_b:
                        x, y = map(int, coords_b.split(","))
                        pyautogui.moveTo(x, y, duration=0.5)
                        pyautogui.doubleClick()
                        return f"Playing song '{search_name}' (Global Search via Artwork Double-Click)."
                        
                    logger.warning("vision_fallback_failed", reason="coords_not_found", target=target_desc_b)
                    
                except Exception as ve:
                    logger.warning("vision_fallback_failed", error=str(ve))

                return f"Song '{search_name}' not in Library. Global search opened. Please click play manually if not started."
            except Exception as e2:
                return f"Music Error: Song '{song_name}' not found locally (even after fuzzy search) and fallback failed: {e2}"

        else:
            script = f'tell application "Music" to {cmd_map[action]}'
            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            if res.returncode != 0:
                return f"Music Error: {res.stderr}"
            return f"Music: {action}"
            
    except Exception as e:
        return f"Music Error: {str(e)}"

@tool
def set_volume(level: int) -> str:
    """
    Set system volume (0-100).
    Args:
        level: Integer between 0 and 100.
    """
    if not (0 <= level <= 100):
        return "Level must be 0-100"
    
    try:
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        return f"Volume set to {level}%"
    except Exception as e:
        return f"Volume Error: {str(e)}"

@tool
def wifi_control(status: str) -> str:
    """
    Turn WiFi on or off.
    Args:
        status: 'on' or 'off'.
    """
    if status not in ['on', 'off']:
        return "Status must be 'on' or 'off'"
    
    # We need to find the device (usually en0)
    try:
        subprocess.run(["networksetup", "-setairportpower", "en0", status], check=True)
        return f"WiFi turned {status}"
    except Exception as e:
        return f"WiFi Error: {str(e)}"

@tool
def bluetooth_control(status: str) -> str:
    """
    Turn Bluetooth on or off.
    Args:
        status: 'on' or 'off'.
    """
    try:
        val = "1" if status == "on" else "0"
        subprocess.run(["blueutil", "-p", val], check=True)
        return f"Bluetooth turned {status}"
    except Exception as e:
        return f"Bluetooth Error: {str(e)}"
