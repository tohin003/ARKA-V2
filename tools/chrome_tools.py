"""
tools/chrome_tools.py — ARKA Chrome Browser Tools

10 agent tools that give ARKA full control of Chrome
via the Browser Bridge WebSocket extension.
"""

from smolagents import tool
import structlog
import json

logger = structlog.get_logger()


def _bridge():
    """Get the browser bridge singleton."""
    from core.browser_bridge import browser_bridge
    return browser_bridge


def _format_result(result: dict) -> str:
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
        if isinstance(val, str) and len(val) > 200:
            val = val[:200] + "…"
        elif isinstance(val, (dict, list)):
            val = json.dumps(val, indent=2)[:500]
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
    return _format_result(result)


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
