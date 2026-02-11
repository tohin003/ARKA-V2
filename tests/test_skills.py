from core.skills import skill_registry

def test_skills():
    print("🧪 Testing Phase 3: Skills Registry...")
    
    # 1. Test Help
    print("\n[1] Testing /help")
    res = skill_registry.execute_skill("/help")
    print(f"Result: {res}")
    if "/commit" in res and "/status" in res:
        print("✅ /help returned available skills.")
    else:
        print("❌ /help failed.")

    # 2. Test Execution (mock status)
    print("\n[2] Testing /status")
    res = skill_registry.execute_skill("/status")
    print(f"Result: {res}")
    # Git status might be "Clean" or "Modified"
    if "Clean" in res or "M " in res or "No changes" in res or "??" in res:
        print("✅ /status executed git command.")
    else:
        print(f"⚠️ /status output unexpected: {res}")

if __name__ == "__main__":
    test_skills()
