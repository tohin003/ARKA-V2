"""
tests/test_mcp.py — Verification for Phase 5.3: MCP Integration

Tests:
1. MCPBridge initializes without errors.
2. Connect to @modelcontextprotocol/server-filesystem.
3. List tools from connected server.
4. Call 'read_file' tool to read a test file.
5. Graceful disconnect.
"""

import sys, os
sys.path.insert(0, os.getcwd())

import time
from core.mcp_client import MCPBridge

def test_mcp_integration():
    results = {
        "init": False,
        "connect": False,
        "list_tools": False,
        "call_tool": False,
        "disconnect": False,
    }

    # ─── Setup: Create a test file ────────────────────────────────────
    # macOS resolves /tmp -> /private/tmp, so we use realpath
    test_dir = os.path.realpath("/tmp/arka_mcp_test")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "hello.txt")
    with open(test_file, "w") as f:
        f.write("ARKA MCP Test — Hello from the other side!")

    # ─── Test 1: Init ─────────────────────────────────────────────────
    print("🧪 Test 1: Initializing MCPBridge...")
    bridge = MCPBridge()
    print(f"   Status: {bridge.status}")
    results["init"] = True
    print("   ✅ Init successful!")

    # ─── Test 2: Connect to filesystem server ─────────────────────────
    print("🧪 Test 2: Connecting to @modelcontextprotocol/server-filesystem...")
    try:
        bridge.connect(
            server_name="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", test_dir],
        )
        print(f"   Status: {bridge.status}")
        results["connect"] = True
        print("   ✅ Connected!")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        bridge.disconnect_all()
        return results

    # ─── Test 3: List tools ───────────────────────────────────────────
    print("🧪 Test 3: Listing tools...")
    tools = bridge.list_tools()
    print(f"   Found {len(tools)} tools:")
    for t in tools:
        print(f"     • {t['name']}: {t['description'][:60]}...")
    if len(tools) > 0:
        results["list_tools"] = True
        print("   ✅ Tools listed!")
    else:
        print("   ❌ No tools found.")

    # ─── Test 4: Call tool ────────────────────────────────────────────
    print("🧪 Test 4: Reading test file via MCP...")
    try:
        content = bridge.call_tool("read_file", {"path": test_file})
        print(f"   File content: {content}")
        if "Hello from the other side" in content:
            results["call_tool"] = True
            print("   ✅ File read successfully via MCP!")
        else:
            print(f"   ❌ Unexpected content: {content}")
    except Exception as e:
        print(f"   ❌ Tool call failed: {e}")

    # ─── Test 5: Disconnect ───────────────────────────────────────────
    print("🧪 Test 5: Disconnecting...")
    bridge.disconnect_all()
    if not bridge.status["running"]:
        results["disconnect"] = True
        print("   ✅ Disconnected cleanly!")
    else:
        print("   ❌ Still running after disconnect!")

    # ─── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    if passed == total:
        print("\n🎉 ALL MCP TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed.")
        sys.exit(1)

    # Cleanup
    os.remove(test_file)
    os.rmdir(test_dir)

if __name__ == "__main__":
    test_mcp_integration()
