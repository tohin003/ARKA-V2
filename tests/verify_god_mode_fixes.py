from core.engine import ArkaEngine

def verify_fixes():
    print("🧪 Verifying God Mode Fixes...")
    engine = ArkaEngine()
    
    # 1. Music Fix
    print("\n[1] Testing Music Playback (Direct)")
    try:
        # Agent should now use music_control(action='play', song_name='Navior')
        res = engine.run("Play the song 'Navior' in Apple Music.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # 2. Browser Fix
    print("\n[2] Testing Browser Fallback (Comet -> Default)")
    try:
        # Agent should use open_app("Comet", url="...") and backend should handle fallback
        res = engine.run("Open 'Comet' browser and go to youtube.com/results?search_query=punkrocker.")
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    verify_fixes()
