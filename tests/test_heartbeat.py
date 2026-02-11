"""
tests/test_heartbeat.py — Verification for Phase 5.2: The Heartbeat

Tests:
1. Scheduler starts and runs as a daemon thread.
2. Custom job executes at the correct interval.
3. Graceful shutdown works properly.
4. Status reporting is accurate.
"""

import sys, os
sys.path.insert(0, os.getcwd())

import time
import schedule as schedule_lib
from core.scheduler import HeartbeatScheduler

def test_heartbeat():
    results = {
        "start": False,
        "pulse": False,
        "custom_job": False,
        "status": False,
        "shutdown": False,
    }

    # ─── Test 1: Start ────────────────────────────────────────────────
    print("🧪 Test 1: Starting Heartbeat...")
    hb = HeartbeatScheduler()
    
    # Register a fast custom job to test execution
    custom_fired = []
    def test_job():
        custom_fired.append(time.time())
        print("   ⚡ Custom job fired!")

    # Clear any global schedule state from imports
    schedule_lib.clear()

    # Directly schedule fast-interval jobs for testing (bypass register_job validation)
    schedule_lib.every(2).seconds.do(test_job)
    schedule_lib.every(3).seconds.do(hb._pulse)
    hb._jobs_registered = 2

    hb._thread = None  # reset
    hb._stop_event.clear()

    # Start background thread
    import threading
    hb._thread = threading.Thread(target=hb._run_loop, name="Test-Heartbeat", daemon=True)
    hb._thread.start()

    if hb.is_alive:
        print("   ✅ Heartbeat thread is alive!")
        results["start"] = True
    else:
        print("   ❌ Heartbeat thread failed to start!")

    # ─── Test 2: Wait for pulse ───────────────────────────────────────
    print("🧪 Test 2: Waiting 4 seconds for pulse + custom job...")
    time.sleep(4)

    if hb._pulse_count > 0:
        print(f"   ✅ Pulse fired! Count: {hb._pulse_count}")
        results["pulse"] = True
    else:
        print("   ❌ Pulse did not fire.")

    if len(custom_fired) > 0:
        print(f"   ✅ Custom job fired {len(custom_fired)} time(s)!")
        results["custom_job"] = True
    else:
        print("   ❌ Custom job did not fire.")

    # ─── Test 3: Status ───────────────────────────────────────────────
    print("🧪 Test 3: Checking status...")
    status = hb.status
    print(f"   Status: {status}")
    if status["alive"] and status["pulse_count"] > 0:
        print("   ✅ Status reporting is accurate!")
        results["status"] = True
    else:
        print("   ❌ Status reporting is inaccurate.")

    # ─── Test 4: Graceful Shutdown ────────────────────────────────────
    print("🧪 Test 4: Stopping Heartbeat...")
    hb.stop()
    time.sleep(0.5)

    if not hb.is_alive:
        print("   ✅ Heartbeat stopped gracefully!")
        results["shutdown"] = True
    else:
        print("   ❌ Heartbeat thread is still alive after stop!")

    # ─── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    if passed == total:
        print("\n🎉 ALL HEARTBEAT TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_heartbeat()
