#!/usr/bin/env python3
"""
tests/test_phase7.py — Phase 7: Chrome Extension Browser Bridge Tests

Validates:
  1. Browser Bridge (WebSocket server lifecycle + command API)
  2. Chrome Tools (all 11 tools registered, correct error handling)
  3. Extension files (manifest, background, content)
  4. Engine Integration (34 total tools)
"""

import sys
import os
import json
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = []


def section(title):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print(f"{'═' * 60}")


def log_test(name, passed, detail=""):
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))
    results.append((name, passed))


def run_tests():
    
    # ══════════════════════════════════════════════════════════════════
    # 1. BROWSER BRIDGE
    # ══════════════════════════════════════════════════════════════════
    section("BROWSER BRIDGE")

    try:
        from core.browser_bridge import BrowserBridge

        # Test instantiation
        bridge = BrowserBridge(port=7778)  # Use different port for testing
        log_test("Bridge instantiation", True, f"port={bridge.port}")

        # Test initial state
        log_test("Initial state: disconnected", 
                 not bridge.is_connected, 
                 f"connected={bridge.is_connected}")

        # Test start (server should listen)
        bridge.start()
        time.sleep(0.5)  # Wait for server thread
        log_test("Server started", 
                 bridge._thread is not None and bridge._thread.is_alive(),
                 "Background thread running")

        # Test command without extension (should return error)
        result = bridge.send_command("navigate", {"url": "test.com"}, timeout=1)
        log_test("Command without extension → error", 
                 result["status"] == "error",
                 result.get("error", "")[:60])

        # Test auth flow
        bridge._auth_waiting = True
        bridge._auth_url = "https://accounts.google.com"
        result = bridge.send_command("click", {"selector": "a"}, timeout=1)
        log_test("Auth waiting blocks commands",
                 result["status"] == "auth_required",
                 "blocked during auth")

        # Test continue after auth
        result = bridge.send_command("continue_after_auth")
        log_test("Continue after auth",
                 result["status"] == "ok" and not bridge._auth_waiting,
                 "auth_waiting cleared")

        # Test status
        status = bridge.status()
        log_test("Status dict", 
                 "connected" in status and "port" in status,
                 f"keys: {list(status.keys())}")

        # Stop
        bridge.stop()
        time.sleep(0.3)
        log_test("Bridge stopped", True)

    except Exception as e:
        log_test("Browser Bridge", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 2. CHROME TOOLS
    # ══════════════════════════════════════════════════════════════════
    section("CHROME TOOLS")

    try:
        from tools.chrome_tools import (
            chrome_navigate, chrome_click, chrome_type, chrome_scroll,
            chrome_screenshot, chrome_get_dom, chrome_get_text,
            chrome_list_tabs, chrome_new_tab, chrome_switch_tab, chrome_continue
        )

        tool_list = [
            chrome_navigate, chrome_click, chrome_type, chrome_scroll,
            chrome_screenshot, chrome_get_dom, chrome_get_text,
            chrome_list_tabs, chrome_new_tab, chrome_switch_tab, chrome_continue
        ]
        log_test(f"All 11 tools importable", len(tool_list) == 11, f"count={len(tool_list)}")

        # Verify each tool has correct attributes
        for t in tool_list:
            assert hasattr(t, 'name'), f"{t} missing .name"
            assert hasattr(t, 'description'), f"{t} missing .description"
        log_test("All tools have name + description", True)

        # Test tools return error when bridge disconnected
        result = chrome_navigate("test.com")
        log_test("Navigate without bridge → error",
                 "not connected" in result.lower() or "error" in result.lower(),
                 result[:60])

        result = chrome_click("#btn")
        log_test("Click without bridge → error",
                 "not connected" in result.lower() or "error" in result.lower(),
                 result[:60])

        result = chrome_list_tabs()
        log_test("List tabs without bridge → error",
                 "not connected" in result.lower() or "error" in result.lower(),
                 result[:60])

    except Exception as e:
        log_test("Chrome Tools import", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # 3. EXTENSION FILES
    # ══════════════════════════════════════════════════════════════════
    section("EXTENSION FILES")

    ext_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extension")

    # Manifest
    manifest_path = os.path.join(ext_dir, "manifest.json")
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        log_test("manifest.json valid JSON", True)
        log_test("Manifest V3", manifest.get("manifest_version") == 3, f"v{manifest.get('manifest_version')}")
        log_test("Has required permissions", 
                 "tabs" in manifest.get("permissions", []) and "scripting" in manifest.get("permissions", []),
                 str(manifest.get("permissions")))
        log_test("Has service worker", 
                 "background" in manifest and "service_worker" in manifest["background"],
                 manifest.get("background", {}).get("service_worker"))
        log_test("Has content scripts", 
                 "content_scripts" in manifest,
                 f"{len(manifest.get('content_scripts', []))} scripts")
    except Exception as e:
        log_test("manifest.json", False, str(e))

    # Background.js
    bg_path = os.path.join(ext_dir, "background.js")
    log_test("background.js exists", os.path.exists(bg_path))
    if os.path.exists(bg_path):
        with open(bg_path) as f:
            bg_content = f.read()
        log_test("Has WebSocket connect", "WebSocket" in bg_content)
        log_test("Has auth detection", "AUTH_PATTERNS" in bg_content or "checkAuthPage" in bg_content)
        log_test("Has command router", "handleCommand" in bg_content)

    # Content.js
    cs_path = os.path.join(ext_dir, "content.js")
    log_test("content.js exists", os.path.exists(cs_path))
    if os.path.exists(cs_path):
        with open(cs_path) as f:
            cs_content = f.read()
        log_test("Has click handler", "handleClick" in cs_content)
        log_test("Has type handler", "handleType" in cs_content)
        log_test("Has DOM serializer", "serializeDOM" in cs_content)

    # Icons
    for size in [16, 48, 128]:
        icon_path = os.path.join(ext_dir, "icons", f"icon{size}.png")
        log_test(f"icon{size}.png exists", os.path.exists(icon_path))

    # Popup
    log_test("popup.html exists", os.path.exists(os.path.join(ext_dir, "popup.html")))
    log_test("popup.js exists", os.path.exists(os.path.join(ext_dir, "popup.js")))

    # ══════════════════════════════════════════════════════════════════
    # 4. ENGINE INTEGRATION
    # ══════════════════════════════════════════════════════════════════
    section("ENGINE INTEGRATION (Phase 7)")

    try:
        from core.engine import ArkaEngine
        engine = ArkaEngine()
        
        tool_names = [t.name for t in engine.tools.values()]

        # Check chrome tools registered
        chrome_tool_names = [
            "chrome_navigate", "chrome_click", "chrome_type", "chrome_scroll",
            "chrome_screenshot", "chrome_get_dom", "chrome_get_text",
            "chrome_list_tabs", "chrome_new_tab", "chrome_switch_tab", "chrome_continue"
        ]
        missing = [t for t in chrome_tool_names if t not in tool_names]
        log_test("All 11 chrome tools registered",
                 len(missing) == 0,
                 f"Missing: {missing}" if missing else "All present")

        total = len(tool_names)
        log_test(f"Total tools: {total}", total >= 34, f"Expected ≥34, got {total}")

    except Exception as e:
        log_test("Engine integration", False, str(e))

    # ══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════════
    section("SUMMARY")
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\n  Results: {passed}/{total}")
    
    if passed == total:
        print(f"\n{'═' * 60}")
        print(f"  🎉 ALL {total}/{total} PHASE 7 TESTS PASSED!")
        print(f"{'═' * 60}")
    else:
        failed = [name for name, p in results if not p]
        print(f"\n  Failed: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
