"""
tools/chrome_tools.py — ARKA Chrome Browser Tools

10 agent tools that give ARKA full control of Chrome
via the Browser Bridge WebSocket extension.
"""

from smolagents import tool
import structlog
import json
from core.session_context import session_context

logger = structlog.get_logger()


def _bridge():
    """Get the browser bridge singleton."""
    from core.browser_bridge import browser_bridge
    return browser_bridge


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _format_result(result: dict, max_string: int = 400, max_json: int = 2000) -> str:
    """Format a bridge result for the agent."""
    if not result:
        return "No response from extension"
    
    status = result.get("status", "unknown")
    
    if status == "error":
        return f"❌ Browser Error: {result.get('error', 'Unknown error')}"
    
    if status == "auth_required":
        return f"⏸ LOGIN REQUIRED: {result.get('message', 'Please log in manually.')} — Tell the user to log in, then use chrome_continue() to resume."
    
    # Build friendly output
    parts = []
    for key, val in result.items():
        if key in ("status", "id"):
            continue
        if isinstance(val, str) and len(val) > max_string:
            val = val[:max_string] + "…"
        elif isinstance(val, (dict, list)):
            dumped = json.dumps(val, indent=2)
            dumped = _truncate(dumped, max_json)
            val = dumped
        parts.append(f"{key}: {val}")
    
    return "\n".join(parts) if parts else f"✅ {status}"


# ═══════════════════════════════════════════════════════════════════════
# NAVIGATION
# ═══════════════════════════════════════════════════════════════════════

@tool
def chrome_navigate(url: str) -> str:
    """
    Navigate the active Chrome tab to a URL.
    If a login page is detected, ARKA will pause and ask for user help.
    
    Args:
        url: The URL to navigate to (e.g., "google.com" or "https://github.com").
    """
    result = _bridge().send_command("navigate", {"url": url})
    if result.get("status") == "ok":
        session_context.update_browser(url=result.get("url"), title=result.get("title"))
    return _format_result(result)


@tool
def chrome_status() -> str:
    """
    Return the Chrome bridge connection status.
    Useful before attempting DOM-based actions.
    """
    status = _bridge().status()
    return json.dumps(status, indent=2)


@tool
def chrome_wait_for_connection(timeout_s: int = 10, poll_interval_s: float = 0.5) -> str:
    """
    Wait for the Chrome bridge to become connected.
    Useful right after launching Chrome.
    
    Args:
        timeout_s: Max seconds to wait.
        poll_interval_s: Seconds between checks.
    """
    import time
    start = time.time()
    while time.time() - start < timeout_s:
        if _bridge().is_connected:
            return "✅ Chrome bridge connected."
        time.sleep(poll_interval_s)
    status = _bridge().status()
    return f"❌ Chrome bridge not connected after {timeout_s}s. Status: {json.dumps(status)}"


# ═══════════════════════════════════════════════════════════════════════
# DOM INTERACTION
# ═══════════════════════════════════════════════════════════════════════

@tool
def chrome_click(selector: str, text: str = None, index: int = 0) -> str:
    """
    Click an element in the active Chrome tab.
    You can target by CSS selector OR by visible text.
    
    Args:
        selector: CSS selector (e.g., "#submit-btn", "a.nav-link", "button").
                  Set to empty string "" if using 'text' instead.
        text: Alternative: find element by its visible text content.
        index: If multiple elements match, click the Nth one (0-indexed).
    """
    params = {"index": index}
    if text:
        params["text"] = text
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("click", params)
    return _format_result(result)


@tool
def chrome_click_at(x: int, y: int, button: str = "left", double: bool = False, page: bool = False) -> str:
    """
    Click at a precise coordinate in the active Chrome tab.
    Coordinates are viewport-based by default. Set page=True to use page coordinates.
    
    Args:
        x: X coordinate (int).
        y: Y coordinate (int).
        button: "left", "right", or "middle".
        double: If True, double-click.
        page: If True, treat x/y as page coords (will scroll into view).
    """
    params = {"x": x, "y": y, "button": button, "double": double, "page": page}
    result = _bridge().send_command("click_at", params)
    return _format_result(result)


@tool
def chrome_focus(selector: str = None, text: str = None, index: int = 0) -> str:
    """
    Focus an element in the active Chrome tab by selector or visible text.
    
    Args:
        selector: CSS selector (e.g., "#email", "input[name='q']").
        text: Visible text to match if selector is not provided.
        index: If multiple matches, focus the Nth one (0-indexed).
    """
    params = {"index": index}
    if selector:
        params["selector"] = selector
    if text:
        params["text"] = text
    result = _bridge().send_command("focus", params)
    return _format_result(result)


@tool
def chrome_press_key(key: str = "Enter", selector: str = None) -> str:
    """
    Press a key in the active Chrome tab (optionally on a target element).
    
    Args:
        key: Key name (e.g., "Enter", "Tab", "Escape", "a").
        selector: CSS selector to focus before pressing.
    """
    params = {"key": key}
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("press_key", params)
    return _format_result(result)


@tool
def chrome_wait_for_selector(selector: str, timeout_ms: int = 5000) -> str:
    """
    Wait until a selector appears in the DOM.
    
    Args:
        selector: CSS selector to wait for.
        timeout_ms: Max time to wait in milliseconds.
    """
    params = {"selector": selector, "timeout_ms": timeout_ms}
    result = _bridge().send_command("wait_for_selector", params, timeout=max(1, (timeout_ms // 1000) + 2))
    return _format_result(result)


@tool
def chrome_type(text: str, selector: str = None, clear: bool = True) -> str:
    """
    Type text into an input field in the active Chrome tab.
    If no selector is given, types into the currently focused field.
    
    Args:
        text: The text to type.
        selector: CSS selector of the input field (e.g., "#search-input", "input[name='q']").
                  If omitted, types into the focused element.
        clear: If True, clears the field before typing. Default: True.
    """
    params = {"text": text, "clear": clear}
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("type", params)
    return _format_result(result)


@tool
def chrome_scroll(direction: str = "down", amount: int = 500) -> str:
    """
    Scroll the page in the active Chrome tab.
    
    Args:
        direction: "down", "up", "left", "right", "top", or "bottom".
        amount: Pixels to scroll (default 500). Ignored for "top"/"bottom".
    """
    result = _bridge().send_command("scroll", {"direction": direction, "amount": amount})
    return _format_result(result)


# ═══════════════════════════════════════════════════════════════════════
# PAGE DATA
# ═══════════════════════════════════════════════════════════════════════

@tool
def chrome_screenshot() -> str:
    """
    Take a screenshot of the visible area in the active Chrome tab.
    Returns the screenshot as a base64 data URL.
    """
    result = _bridge().send_command("screenshot")
    if result.get("status") == "ok" and result.get("screenshot"):
        # Return a short confirmation + the data URL (agent can use it)
        data_url = result["screenshot"]
        return f"📸 Screenshot captured ({len(data_url)} bytes). Data URL available."
    return _format_result(result)


@tool
def chrome_get_dom(selector: str = None, max_depth: int = 3) -> str:
    """
    Extract the DOM tree of the active Chrome tab.
    Returns a simplified JSON tree with tags, ids, classes, text, and links.
    
    Args:
        selector: CSS selector to scope the extraction (e.g., "#main", "article").
                  If omitted, extracts from <body>.
        max_depth: Maximum depth of the DOM tree (default 3).
    """
    params = {"max_depth": max_depth}
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("get_dom", params)
    if result.get("status") == "ok":
        session_context.update_browser(url=result.get("url"), title=result.get("title"))
        payload = {
            "title": result.get("title"),
            "url": result.get("url"),
            "dom": result.get("dom"),
        }
        return _truncate(json.dumps(payload, indent=2), 12000)
    return _format_result(result)


@tool
def chrome_get_text(selector: str = None, max_length: int = 5000) -> str:
    """
    Get the visible text content of the active Chrome tab.
    
    Args:
        selector: CSS selector to scope the text (e.g., "#content", "article").
                  If omitted, gets all visible text.
        max_length: Maximum characters to return (default 5000).
    """
    params = {"max_length": max_length}
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("get_text", params)
    if result.get("status") == "ok":
        session_context.update_browser(url=result.get("url"), title=result.get("title"))
        return result.get("text", "")
    return _format_result(result)


@tool
def chrome_verify_text(text: str, selector: str = None, max_length: int = 5000) -> str:
    """
    Verify that visible page text contains the given string.
    Useful for confirming comments/messages actually appeared.
    
    Args:
        text: Text to verify.
        selector: Optional CSS selector to scope the search.
        max_length: Max characters to fetch.
    """
    params = {"max_length": max_length}
    if selector:
        params["selector"] = selector
    result = _bridge().send_command("get_text", params)
    if result.get("status") == "ok":
        session_context.update_browser(url=result.get("url"), title=result.get("title"))
        hay = result.get("text", "") or ""
        if text in hay:
            return f"✅ Verified text present: {text}"
        return f"❌ Text not found: {text}"
    return _format_result(result)


@tool
def chrome_get_elements(selector: str, max_results: int = 20) -> str:
    """
    Get a list of elements that match a selector, including bounding boxes.
    
    Args:
        selector: CSS selector to match elements.
        max_results: Max number of results to return.
    """
    params = {"selector": selector, "max_results": max_results}
    result = _bridge().send_command("get_elements", params)
    if result.get("status") == "ok":
        return _truncate(json.dumps(result, indent=2), 12000)
    return _format_result(result)


# ═══════════════════════════════════════════════════════════════════════
# TAB MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

@tool
def chrome_list_tabs() -> str:
    """
    List all open Chrome tabs with their IDs, titles, URLs, and active status.
    Use the tab ID with chrome_switch_tab to switch tabs.
    """
    result = _bridge().send_command("list_tabs")
    if result.get("status") == "ok" and result.get("tabs"):
        lines = []
        for tab in result["tabs"]:
            active_marker = " ← active" if tab.get("active") else ""
            lines.append(f"  [{tab['id']}] {tab.get('title', '?')[:50]} — {tab.get('url', '?')[:60]}{active_marker}")
        return f"Open tabs ({len(result['tabs'])}):\n" + "\n".join(lines)
    return _format_result(result)


@tool
def chrome_new_tab(url: str = None) -> str:
    """
    Open a new Chrome tab, optionally navigating to a URL.
    
    Args:
        url: URL to open in the new tab. If omitted, opens a blank tab.
    """
    params = {}
    if url:
        params["url"] = url
    result = _bridge().send_command("new_tab", params)
    if result.get("status") == "ok":
        session_context.update_browser(url=url, title=result.get("title"))
    return _format_result(result)


@tool
def chrome_switch_tab(tab_id: int) -> str:
    """
    Switch to a specific Chrome tab by its ID.
    Use chrome_list_tabs() first to get tab IDs.
    
    Args:
        tab_id: The numeric tab ID to switch to.
    """
    result = _bridge().send_command("switch_tab", {"tab_id": tab_id})
    if result.get("status") == "ok":
        session_context.update_browser(url=result.get("url"), title=result.get("title"))
    return _format_result(result)


# ═══════════════════════════════════════════════════════════════════════
# AUTH FLOW
# ═══════════════════════════════════════════════════════════════════════

@tool
def chrome_continue() -> str:
    """
    Resume browser operations after the user has completed a login/authentication.
    Call this ONLY after the user confirms they have logged in.
    """
    result = _bridge().send_command("continue_after_auth")
    return _format_result(result)
