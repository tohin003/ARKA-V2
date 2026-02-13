from __future__ import annotations

from typing import Iterable

from core.session_context import session_context
import ast


SUCCESS_MARKERS = [
    "success",
    "successfully",
    "done",
    "completed",
    "sent",
    "opened",
    "playing",
    "shared",
]

BROWSER_MARKERS = [
    "browser",
    "tab",
    "website",
    "youtube",
    "instagram",
    "chrome",
    "comet",
]

VERIFY_CALLS = [
    "chrome_wait_for_selector",
    "chrome_get_text",
    "chrome_get_dom",
    "chrome_get_elements",
    "chrome_verify_text",
    "find_text_on_screen",
    "find_and_click_text_on_screen",
    "get_screen_coordinates",
]

REQUIRES_STRICT_VERIFY = [
    "comment",
    "message",
    "dm",
    "share",
    "send",
]

UI_MARKERS = [
    "top section",
    "bottom section",
    "left side",
    "right side",
    "song",
    "track",
    "apple music",
    "music app",
]


def _iter_action_steps(memory) -> Iterable:
    for step in getattr(memory, "steps", []):
        # ActionStep has "code_action" attribute
        if hasattr(step, "code_action"):
            yield step


def _has_error(memory) -> bool:
    for step in _iter_action_steps(memory):
        if getattr(step, "error", None):
            return True
        obs = (getattr(step, "observations", None) or "")
        if "❌" in obs or "Browser Error" in obs or "Timeout" in obs or "Error" in obs:
            return True
    return False


def _has_verification(memory) -> bool:
    for step in _iter_action_steps(memory):
        code = getattr(step, "code_action", None) or ""
        for name in VERIFY_CALLS:
            if name in code:
                return True
    return False


def _claims_success(final_answer: str) -> bool:
    text = final_answer.lower()
    return any(m in text for m in SUCCESS_MARKERS)


def _is_browser_task(task: str) -> bool:
    text = (task or "").lower()
    if any(m in text for m in BROWSER_MARKERS):
        return True
    if session_context.last_site or session_context.last_url:
        return True
    return False


def _requires_strict(task: str) -> bool:
    text = (task or "").lower()
    if any(k in text for k in REQUIRES_STRICT_VERIFY):
        return True
    if any(k in text for k in UI_MARKERS) and session_context.last_app:
        return True
    return False


def _has_strict_verification(memory) -> bool:
    for step in _iter_action_steps(memory):
        code = getattr(step, "code_action", None) or ""
        if "chrome_verify_text" in code:
            return True
        if "find_text_on_screen" in code or "find_and_click_text_on_screen" in code or "get_screen_coordinates" in code:
            return True
    return False


def build_evidence(memory) -> str:
    """
    Build a compact evidence string from recent action steps.
    Avoids dumping large DOM/text outputs.
    """
    lines = []
    for step in _iter_action_steps(memory):
        code = getattr(step, "code_action", None) or ""
        if code:
            calls = []
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            calls.append(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            calls.append(node.func.attr)
            except Exception:
                pass
            if calls:
                lines.append(f"tools: {', '.join(calls[:8])}")

        obs = getattr(step, "observations", None) or ""
        if "Last output from code snippet:" in obs:
            tail = obs.split("Last output from code snippet:")[-1].strip()
            if tail:
                # Truncate to keep concise
                tail = tail.replace("\n", " ").strip()
                lines.append(f"out: {tail[:300]}")

    return "\n".join(lines[-8:])


def adjust_final_answer(final_answer: str, memory, task: str) -> str:
    """
    Guard against unverified success claims.
    If errors occurred or verification was missing for browser tasks,
    downgrade the response to a cautionary status update.
    """
    if not isinstance(final_answer, str):
        return final_answer

    if not _claims_success(final_answer):
        return final_answer

    if _has_error(memory):
        return (
            "I couldn't verify that the task fully succeeded. "
            "I hit an error during execution. "
            "If you'd like, I can try again or continue from the current state."
        )

    if _requires_strict(task) and not _has_strict_verification(memory):
        return (
            "I ran the steps, but I didn't verify the result. "
            "Please confirm it on the page, or tell me to verify and finish."
        )

    if _is_browser_task(task) and not _has_verification(memory):
        target = session_context.last_site or session_context.last_url or "the current browser tab"
        return (
            "I ran the steps, but I couldn't verify completion with a DOM check. "
            f"Please confirm the result on {target}, or tell me to continue."
        )

    return final_answer
