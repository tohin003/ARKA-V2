import subprocess
import os
import sys
import time
import socket

# List of tests to run in order
TEST_SUITE = [
    ("Phase 0: Hello World", "tests/test_hello_world.py"),
    ("Phase 1: Coding Loop", "tests/test_coding_loop.py"),
    ("Phase 2: God Mode (HW)", "tests/test_god_mode.py"),
    ("Phase 3: Memory & Safety", "tests/test_memory.py"),
    ("Phase 3: Planning Mode", "tests/test_planning.py"),
    ("Phase 3: Skills Registry", "tests/test_skills.py"),
    ("Phase 3: Browser Tool", "tests/test_browser.py"),
    ("Phase 3: Browser Bridge Shutdown", "tests/test_browser_bridge_shutdown.py"),
]

ONLINE_TESTS = {
    "tests/test_hello_world.py",
    "tests/test_coding_loop.py",
    "tests/test_god_mode.py",
    "tests/test_memory.py",
    "tests/test_planning.py",
}

NETWORK_TESTS = ONLINE_TESTS | {"tests/test_browser.py"}

def _network_ok(host: str = "api.openai.com") -> bool:
    try:
        socket.getaddrinfo(host, 443)
        return True
    except Exception:
        return False

def run_test(name, script_path):
    print(f"\n🔵 RUNNING: {name} ({script_path})")
    print("=" * 60)
    
    start_time = time.time()
    try:
        # Run with PYTHONPATH=. to ensure imports work
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        result = subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            timeout=120 # 2 mins max per test
        )
        
        duration = time.time() - start_time
        
        # Check output for explicit success markers or exit code 0
        # (Our tests usually print "✅" on success)
        success = result.returncode == 0 and ("✅" in result.stdout or "TEST PASSED" in result.stdout)
        
        if success:
            print(f"🟢 PASSED ({duration:.2f}s)")
            return True, result.stdout
        else:
            print(f"🔴 FAILED ({duration:.2f}s)")
            print("--- STDOUT ---")
            print(result.stdout)
            print("--- STDERR ---")
            print(result.stderr)
            return False, result.stdout + "\n" + result.stderr

    except Exception as e:
        print(f"🔴 CRASHED: {str(e)}")
        return False, str(e)

def main():
    print("🚀 STARTING ARKA V2 FULL REGRESSION SUITE")
    print(f"Directory: {os.getcwd()}")

    online_requested = os.environ.get("ARKA_OFFLINE", "0") != "1"
    network_ok = _network_ok()
    if online_requested and not network_ok:
        print("⚠️ Network/DNS unavailable. Network-dependent tests will be skipped.")
    
    results = []
    
    for name, script in TEST_SUITE:
        if not os.path.exists(script):
            print(f"⚠️ SKIPPING {name}: File not found ({script})")
            results.append((name, "SKIPPING (Not Found)"))
            continue
            
        if online_requested and not network_ok and script in NETWORK_TESTS:
            print(f"⚠️ SKIPPING {name}: network unavailable.")
            results.append((name, "SKIP"))
            continue

        passed, output = run_test(name, script)
        status = "PASS" if passed else "FAIL"
        results.append((name, status))
        
        # Optional: Fail fast? No, let's run all to see full state.
        
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, status in results:
        if status == "SKIP":
            icon = "⚪"
        else:
            icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} {name}: {status}")
        if status == "FAIL":
            all_passed = False
            
    if all_passed:
        print("\n✨ ALL SYSTEMS OPERATIONAL. READY FOR UI BUILD.")
        sys.exit(0)
    else:
        print("\n⚠️ SOME SYSTEMS FAILED. DIAGNOSTICS REQUIRED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
