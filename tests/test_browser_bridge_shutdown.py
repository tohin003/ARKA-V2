import socket
import time

from core.browser_bridge import BrowserBridge


def _get_free_port() -> int:
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port
    except PermissionError:
        s.close()
        return 0


def test_browser_bridge_shutdown():
    print("🧪 Testing Browser Bridge clean shutdown...")

    port = _get_free_port()
    if port == 0:
        print("✅ Skipped (socket bind not permitted in sandbox).")
        return
    bridge = BrowserBridge(port=port, host="127.0.0.1")

    try:
        bridge.start()
        time.sleep(0.2)

        if bridge.status().get("last_error"):
            print(f"❌ Bridge failed to start: {bridge.status()['last_error']}")
            return

    finally:
        bridge.stop()

    # Validate shutdown state
    if bridge._thread is not None and bridge._thread.is_alive():
        print("❌ Bridge thread still alive after stop().")
        return
    if bridge._loop is not None:
        print("❌ Event loop not cleared after stop().")
        return
    if bridge._pending:
        print("❌ Pending futures not cleared after stop().")
        return
    if bridge.connected:
        print("❌ Bridge still marked connected after stop().")
        return

    print("✅ Browser bridge shutdown clean.")


if __name__ == "__main__":
    test_browser_bridge_shutdown()
