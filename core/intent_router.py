import re
from typing import Optional, List

from tools.hardware import music_control, set_volume, wifi_control, bluetooth_control
from tools.system import open_app
from tools.messaging import send_whatsapp_message, send_whatsapp_web_message
from tools.chrome_tools import chrome_wait_for_connection, chrome_navigate
from tools.todo import todo_add, todo_list, todo_complete
from tools.search import web_search
from tools.codebase_graph import generate_graph
from tools.git import git_status, git_commit
from tools.terminal import run_terminal
from tools.memory_tools import (
    remember_fact,
    memory_search,
    memory_forget,
    memory_lock,
    memory_export,
    memory_stats,
)
from tools.goal_tools import list_goals, advance_goal, complete_goal
from tools.mcp_tools import list_mcp_tools, call_mcp_tool
from tools.browser import visit_page
from tools.dev import read_file, write_file, grep
from tools.system import system_click, system_click_at, system_type, system_press, system_hotkey
from tools.vision import find_text_on_screen, find_and_click_text_on_screen, get_screen_coordinates
from tools.chrome_tools import (
    chrome_click,
    chrome_type,
    chrome_press_key,
    chrome_scroll,
    chrome_screenshot,
    chrome_get_text,
    chrome_verify_text,
    chrome_list_tabs,
    chrome_new_tab,
    chrome_switch_tab,
)
from memory.mistakes import mistake_guard


APP_ALIASES = {
    "apple music": "Apple Music",
    "music": "Music",
    "calculator": "Calculator",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "safari": "Safari",
    "whatsapp": "WhatsApp",
}


def _split_contacts(raw: str) -> List[str]:
    if not raw:
        return []
    parts = re.split(r"\s*(?:,| and | & |;)+\s*", raw.strip(), flags=re.IGNORECASE)
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned if cleaned else [raw.strip()]


def _extract_message_and_contacts(task: str) -> Optional[tuple[str, str]]:
    lower = task.lower()
    if "send " not in lower or " to " not in lower:
        return None

    send_idx = lower.find("send ")
    fragment = task[send_idx + 5 :].strip()
    frag_lower = fragment.lower()

    # Find last ' to ' in fragment
    matches = list(re.finditer(r"\bto\b", frag_lower))
    if not matches:
        return None
    last = matches[-1]
    msg = fragment[: last.start()].strip()
    contacts = fragment[last.end() :].strip()
    if not msg or not contacts:
        return None
    return msg, contacts


def _browser_requested(lower: str) -> bool:
    return any(k in lower for k in ["browser", "web", "whatsapp.com", "in chrome", "in the browser"])


def _extract_url(task: str) -> Optional[str]:
    # Prefer explicit http(s)
    m = re.search(r"https?://\S+", task)
    if m:
        return m.group(0).rstrip(".,)")
    # Fallback to domain-like
    m = re.search(r"\b([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}\b", task)
    if m:
        return m.group(0)
    return None


def _navigate(url: str) -> str:
    status = chrome_wait_for_connection()
    if "❌" in status:
        # Fallback to Playwright if Chrome bridge isn't connected
        return visit_page(url)
    if not url.startswith("http"):
        url = "https://" + url
    return chrome_navigate(url)


def _extract_song(task: str) -> Optional[str]:
    m = re.search(r"\bplay\s+(.+)$", task, flags=re.IGNORECASE)
    if not m:
        return None
    song = m.group(1).strip()
    # Remove trailing qualifiers
    song = re.sub(r"\s+(song|music|track)$", "", song, flags=re.IGNORECASE).strip()
    song = re.sub(r"\s+on\s+apple\s+music$", "", song, flags=re.IGNORECASE).strip()
    song = re.sub(r"\s+in\s+apple\s+music$", "", song, flags=re.IGNORECASE).strip()
    return song if song else None


def _extract_quoted(text: str) -> Optional[str]:
    m = re.search(r"['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def _parse_hotkey(text: str) -> Optional[List[str]]:
    # Accept formats like "cmd+f", "command+shift+p"
    m = re.search(r"(?:hotkey|press)\s+([a-zA-Z0-9+\- ]+)$", text, flags=re.IGNORECASE)
    if not m:
        return None
    combo = m.group(1).strip().lower()
    combo = combo.replace("command", "command").replace("cmd", "command").replace("control", "ctrl")
    # Split on + or spaces
    parts = re.split(r"[+\s]+", combo)
    parts = [p for p in parts if p]
    if len(parts) >= 2:
        return parts
    return None


def _parse_click_at(text: str) -> Optional[tuple[int, int]]:
    m = re.search(r"click\s+at\s*(\d+)\s*,\s*(\d+)", text, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"click\s*(\d+)\s*,\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def try_handle(task: str) -> Optional[str]:
    if not task:
        return None
    lower = task.lower().strip()
    results: List[str] = []

    # A) Explicit system/screen/vision commands
    click_at = _parse_click_at(task)
    if click_at:
        x, y = click_at
        return system_click_at(x, y)

    if re.search(r"\bclick .+ on screen\b", lower) or lower.startswith("system click") or lower.startswith("screen click"):
        target = re.sub(r"^(system|screen)\s+click\s+", "", task, flags=re.IGNORECASE).strip()
        target = re.sub(r"\s+on screen$", "", target, flags=re.IGNORECASE).strip()
        if target:
            return system_click(target)

    if lower.startswith("find ") and " on screen" in lower:
        query = re.sub(r"^find\s+", "", task, flags=re.IGNORECASE)
        query = re.sub(r"\s+on screen$", "", query, flags=re.IGNORECASE).strip()
        if query:
            return find_text_on_screen(query, region_hint="full screen")

    if re.search(r"\bclick .+ on screen\b", lower) or lower.startswith("click "):
        if "on screen" in lower:
            query = re.sub(r"^click\s+", "", task, flags=re.IGNORECASE)
            query = re.sub(r"\s+on screen$", "", query, flags=re.IGNORECASE).strip()
            if query:
                return find_and_click_text_on_screen(query, region_hint="full screen")

    if lower.startswith("system type") or lower.startswith("screen type") or "type on screen" in lower:
        text = _extract_quoted(task) or re.sub(r"^(system|screen)\s+type\s+", "", task, flags=re.IGNORECASE)
        text = re.sub(r"\s+on screen$", "", text, flags=re.IGNORECASE).strip()
        if text:
            return system_type(text)

    hotkey = _parse_hotkey(task)
    if hotkey and ("hotkey" in lower or "press" in lower) and ("browser" not in lower and "chrome" not in lower):
        return system_hotkey(hotkey)

    if lower.startswith("press ") and ("browser" not in lower and "chrome" not in lower):
        key = re.sub(r"^press\s+", "", task, flags=re.IGNORECASE).strip()
        if key:
            return system_press(key)

    # B) Chrome/browser explicit commands
    if lower.startswith("chrome ") or lower.startswith("browser "):
        if "screenshot" in lower:
            return chrome_screenshot()
        if "list tabs" in lower:
            return chrome_list_tabs()
        if "new tab" in lower:
            url = _extract_url(task)
            return chrome_new_tab(url) if url else chrome_new_tab()
        if "switch tab" in lower:
            m = re.search(r"switch tab\s+(\d+)", lower)
            if m:
                return chrome_switch_tab(int(m.group(1)))
        if "scroll" in lower:
            m = re.search(r"scroll\s+(up|down|left|right|top|bottom)(?:\s+(\d+))?", lower)
            if m:
                direction = m.group(1)
                amount = int(m.group(2)) if m.group(2) else 500
                return chrome_scroll(direction, amount)
        if "press " in lower:
            key = re.sub(r"^.*press\s+", "", task, flags=re.IGNORECASE).strip()
            if key:
                return chrome_press_key(key)
        if "verify text" in lower:
            text = re.sub(r"^.*verify text\s+", "", task, flags=re.IGNORECASE).strip()
            if text:
                return chrome_verify_text(text)
        if "get text" in lower:
            return chrome_get_text()
        if "type " in lower:
            # format: chrome type "text" into selector
            text = _extract_quoted(task)
            selector = None
            m = re.search(r"(?:into|in)\s+([#\\.\\w\\[\\]=\\-]+)$", task)
            if m:
                selector = m.group(1).strip()
            if not text:
                text = re.sub(r"^.*type\s+", "", task, flags=re.IGNORECASE)
                if selector:
                    text = re.sub(r"(?:into|in)\s+.+$", "", text, flags=re.IGNORECASE).strip()
            if text:
                return chrome_type(text, selector=selector)
        if "click " in lower:
            text = re.sub(r"^.*click\s+", "", task, flags=re.IGNORECASE).strip()
            if text:
                return chrome_click("", text=text, index=0)

    # 1) WhatsApp send (browser or desktop)
    msg_contacts = _extract_message_and_contacts(task)
    if msg_contacts and ("whatsapp" in lower or "whats app" in lower):
        message, contacts_raw = msg_contacts
        contacts = _split_contacts(contacts_raw)
        if _browser_requested(lower):
            # Send via web, one-by-one for clarity
            for name in contacts:
                results.append(send_whatsapp_web_message(name, message))
        else:
            for name in contacts:
                results.append(send_whatsapp_message(name, message))
        return "\n".join(results)

    # 2) Open WhatsApp Web
    if ("whatsapp" in lower or "whats app" in lower) and _browser_requested(lower) and "send " not in lower:
        return _navigate("https://web.whatsapp.com")

    # 3) Open URL in browser
    if any(k in lower for k in ["open ", "visit ", "go to ", "navigate "]):
        url = _extract_url(task)
        if url and _browser_requested(lower):
            return _navigate(url)
        if url and not _browser_requested(lower):
            return visit_page(url)

    # 4) Open app
    if lower.startswith("open "):
        app_raw = task[5:].strip().lower()
        for alias, app_name in APP_ALIASES.items():
            if alias in app_raw:
                return open_app(app_name)

    # 5) Music controls
    song = _extract_song(task)
    if song:
        results.append(music_control("play", song_name=song))
        return "\n".join(results)

    if "pause" in lower and "music" in lower:
        return music_control("pause")
    if "next" in lower and "song" in lower:
        return music_control("next")
    if "previous" in lower or "prev" in lower:
        if "song" in lower or "track" in lower:
            return music_control("prev")

    # 6) Volume
    m = re.search(r"\bvolume\b\s*(?:to)?\s*(\d{1,3})", lower)
    if m:
        level = int(m.group(1))
        return set_volume(level)

    # 7) WiFi/Bluetooth
    if "wifi" in lower:
        if any(k in lower for k in ["on", "enable", "turn on"]):
            return wifi_control("on")
        if any(k in lower for k in ["off", "disable", "turn off"]):
            return wifi_control("off")
    if "bluetooth" in lower:
        if any(k in lower for k in ["on", "enable", "turn on"]):
            return bluetooth_control("on")
        if any(k in lower for k in ["off", "disable", "turn off"]):
            return bluetooth_control("off")

    # 8) Todo
    if lower.startswith("todo ") or "add todo" in lower or "add task" in lower:
        task_text = task.split("todo", 1)[-1].strip()
        if not task_text:
            return None
        return todo_add(task_text)
    if "list todos" in lower or "list todo" in lower:
        return todo_list()
    if "complete todo" in lower or "complete task" in lower:
        m = re.search(r"(\d+)", lower)
        if m:
            return todo_complete(int(m.group(1)))

    # 9) Web search
    if lower.startswith("search ") or "search for" in lower or lower.startswith("google "):
        query = re.sub(r"^(search for|search|google)\s+", "", task, flags=re.IGNORECASE).strip()
        if query:
            return web_search(query)

    # 10) Memory
    if lower.startswith("remember that "):
        fact = task[len("remember that ") :].strip()
        if fact:
            return remember_fact(fact)
    if lower.startswith("remember "):
        fact = task[len("remember ") :].strip()
        if fact:
            return remember_fact(fact)
    if "memory search" in lower or "search memory" in lower:
        query = re.sub(r".*(memory search|search memory)\s*", "", task, flags=re.IGNORECASE).strip()
        if query:
            return memory_search(query)
    if lower.startswith("forget memory"):
        m = re.search(r"(\d+)", lower)
        if m:
            return memory_forget(int(m.group(1)))
    if lower.startswith("lock memory"):
        m = re.search(r"(\d+)", lower)
        if m:
            return memory_lock(int(m.group(1)))
    if "memory stats" in lower:
        return memory_stats()
    if "export memory" in lower:
        return memory_export()

    # 11) Goals
    if "list goals" in lower:
        return list_goals()
    if lower.startswith("advance goal"):
        m = re.search(r"advance goal\s+([a-zA-Z0-9]+)", lower)
        if m:
            return advance_goal(m.group(1))
    if lower.startswith("complete goal"):
        m = re.search(r"complete goal\s+([a-zA-Z0-9]+)", lower)
        if m:
            return complete_goal(m.group(1))

    # 12) Codebase graph
    if "generate graph" in lower or "codebase graph" in lower:
        m = re.search(r"(graph|codebase graph)\s+(.+)$", task, flags=re.IGNORECASE)
        path = m.group(2).strip() if m else "."
        return generate_graph(path)

    # 13) Git
    if "git status" in lower or lower.strip() == "status":
        return git_status()
    if lower.startswith("commit ") or lower.startswith("git commit "):
        msg = re.sub(r"^(git\s+commit|commit)\s+", "", task, flags=re.IGNORECASE).strip()
        if msg:
            return git_commit(msg)
    if lower.startswith("checkpoint "):
        msg = task[len("checkpoint ") :].strip()
        if msg:
            return git_commit(msg)

    # 14) Terminal (explicit)
    if lower.startswith("run:") or lower.startswith("execute:") or lower.startswith("cmd:"):
        cmd = task.split(":", 1)[-1].strip()
        if cmd:
            return run_terminal(cmd)
    m = re.search(r"`([^`]+)`", task)
    if m and ("run" in lower or "execute" in lower):
        return run_terminal(m.group(1))

    # 15) MCP
    if "list mcp tools" in lower:
        return list_mcp_tools()
    m = re.search(r"call mcp tool\s+(\w+)\s*(\{.*\})?", task, flags=re.IGNORECASE)
    if m:
        name = m.group(1)
        args = m.group(2) or "{}"
        return call_mcp_tool(name, args)

    # 10) Files
    if lower.startswith("read file") or lower.startswith("open file"):
        path = re.sub(r"^(read|open)\s+file\s+", "", task, flags=re.IGNORECASE).strip()
        if path:
            return read_file(path, line_numbers=True)
    if lower.startswith("write file") or lower.startswith("save file"):
        # write file <path> with <content>
        m = re.search(r"(write|save)\s+file\s+(.+?)\s+with\s+(.+)$", task, flags=re.IGNORECASE | re.DOTALL)
        if m:
            path = m.group(2).strip()
            content = m.group(3).strip()
            return write_file(path, content)
    if lower.startswith("grep "):
        m = re.search(r"grep\s+(.+?)\s+in\s+(.+)$", task, flags=re.IGNORECASE)
        if m:
            pattern = m.group(1).strip()
            path = m.group(2).strip()
            return grep(pattern, path)

    # 11) Memory
    if lower.startswith("remember that "):
        fact = task[len("remember that ") :].strip()
        if fact:
            return remember_fact(fact)
    if lower.startswith("remember "):
        fact = task[len("remember ") :].strip()
        if fact:
            return remember_fact(fact)
    if "memory search" in lower or "search memory" in lower:
        query = re.sub(r".*(memory search|search memory)\s*", "", task, flags=re.IGNORECASE).strip()
        if query:
            return memory_search(query)
    if lower.startswith("forget memory"):
        m = re.search(r"(\d+)", lower)
        if m:
            return memory_forget(int(m.group(1)))
    if lower.startswith("lock memory"):
        m = re.search(r"(\d+)", lower)
        if m:
            return memory_lock(int(m.group(1)))
    if "memory stats" in lower:
        return memory_stats()
    if "export memory" in lower:
        return memory_export()

    # 12) Goals
    if "list goals" in lower:
        return list_goals()
    if lower.startswith("advance goal"):
        m = re.search(r"advance goal\s+([a-zA-Z0-9]+)", lower)
        if m:
            return advance_goal(m.group(1))
    if lower.startswith("complete goal"):
        m = re.search(r"complete goal\s+([a-zA-Z0-9]+)", lower)
        if m:
            return complete_goal(m.group(1))

    # 13) Codebase graph
    if "generate graph" in lower or "codebase graph" in lower:
        m = re.search(r"(graph|codebase graph)\s+(.+)$", task, flags=re.IGNORECASE)
        path = m.group(2).strip() if m else "."
        return generate_graph(path)

    # 14) Git
    if "git status" in lower or lower.strip() == "status":
        return git_status()
    if lower.startswith("commit ") or lower.startswith("git commit "):
        msg = re.sub(r"^(git\s+commit|commit)\s+", "", task, flags=re.IGNORECASE).strip()
        if msg:
            return git_commit(msg)
    if lower.startswith("checkpoint "):
        msg = task[len("checkpoint ") :].strip()
        if msg:
            return git_commit(msg)

    # 15) Terminal (explicit)
    if lower.startswith("run:") or lower.startswith("execute:") or lower.startswith("cmd:"):
        cmd = task.split(":", 1)[-1].strip()
        if cmd:
            guard = mistake_guard.validate_command(cmd)
            if guard:
                return f"❌ {guard}"
            return run_terminal(cmd)
    m = re.search(r"`([^`]+)`", task)
    if m and ("run" in lower or "execute" in lower):
        cmd = m.group(1)
        guard = mistake_guard.validate_command(cmd)
        if guard:
            return f"❌ {guard}"
        return run_terminal(cmd)

    # 16) MCP
    if "list mcp tools" in lower:
        return list_mcp_tools()
    m = re.search(r"call mcp tool\s+(\w+)\s*(\{.*\})?", task, flags=re.IGNORECASE)
    if m:
        name = m.group(1)
        args = m.group(2) or "{}"
        return call_mcp_tool(name, args)

    return None
