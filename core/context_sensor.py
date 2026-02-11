"""
core/context_sensor.py — Context Sensing (Phase 6.4)

Detects the user's current desktop context via AppleScript:
  - Frontmost application name
  - Window title (often contains filename/URL)
  
This is injected into the system prompt so ARKA knows what
you're doing right now without you telling it.
"""

import subprocess
import structlog

logger = structlog.get_logger()


class ContextSensor:
    """Reads the user's current desktop state via AppleScript."""

    def get_context(self) -> dict:
        """
        Returns a dict with current context information.
        Gracefully falls back to unknowns on any failure.
        """
        return {
            "frontmost_app": self._get_frontmost_app(),
            "window_title": self._get_window_title(),
        }

    def _run_osascript(self, script: str) -> str:
        """Execute an AppleScript and return stdout."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.debug("context_sensor_osascript_failed", error=str(e))
            return "unknown"

    def _get_frontmost_app(self) -> str:
        return self._run_osascript(
            'tell application "System Events" to get name of first application process whose frontmost is true'
        )

    def _get_window_title(self) -> str:
        return self._run_osascript(
            'tell application "System Events" to get name of front window of (first application process whose frontmost is true)'
        )

    def format_for_prompt(self) -> str:
        """Format context for injection into system prompt."""
        ctx = self.get_context()
        app = ctx["frontmost_app"]
        title = ctx["window_title"]
        
        if app == "unknown" and title == "unknown":
            return ""
        
        lines = ["## 🖥️ CURRENT CONTEXT"]
        lines.append(f"- Active App: {app}")
        if title != "unknown":
            lines.append(f"- Window: {title}")
        return "\n".join(lines)


# Singleton
context_sensor = ContextSensor()
