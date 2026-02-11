from core.engine import ArkaEngine
import sys

def verify_strict():
    print("🛡️ STRICT TOOL VERIFICATION")
    engine = ArkaEngine()
    
    # Test 1: Music Failure (Non-existent song)
    print("\n[1] Testing Music Failure (Expecting Error)")
    res = engine.run("Play the song 'NONEXISTENT_SONG_XYZ123' in Apple Music.")
    print(f"Result: {res}")
    
    if "Error" not in str(res) and "not found" not in str(res):
        print("❌ FAILED: Song playback fake-succeeded!")
        sys.exit(1) # Strict exit
    else:
        print("✅ PASS: Correctly reported error.")

    # Test 2: Browser Fallback
    print("\n[2] Testing Browser Fallback (Comet)")
    res = engine.run("Open 'Comet' browser and go to youtube.com.")
    print(f"Result: {res}")
    
    if "Could not find" in str(res) or "Opened default" in str(res) or "opened https" in str(res):
        print("✅ PASS: Correctly handled fallback.")
    elif "Error" in str(res):
        print("✅ PASS: Correctly reported error (if fallback not triggered).")
    else:
         # If it says "Opened Comet", it lied.
         if "Opened Comet" in str(res) and "default" not in str(res):
             print("❌ FAILED: Claimed to open Comet!")
             sys.exit(1)
         print("✅ PASS (Ambiguous result but no lie detected).")

    print("\n🎉 Strict Verification Passed.")

if __name__ == "__main__":
    verify_strict()
