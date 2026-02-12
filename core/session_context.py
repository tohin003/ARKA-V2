import os
from urllib.parse import urlparse


class SessionContext:
    """
    Tracks short-term session state to improve reference resolution.
    This is not persisted across sessions.
    """

    def __init__(self):
        self.last_app: str | None = None
        self.last_url: str | None = None
        self.last_site: str | None = None
        self.last_title: str | None = None
        self.last_task: str | None = None
        self.last_tool: str | None = None

        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.context_window: int = int(os.getenv("ARKA_CONTEXT_WINDOW", "128000"))

    def update_app(self, app_name: str):
        self.last_app = app_name

    def update_task(self, task: str):
        self.last_task = task

    def update_browser(self, url: str | None = None, title: str | None = None):
        if url:
            self.last_url = url
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    self.last_site = parsed.netloc
            except Exception:
                pass
        if title:
            self.last_title = title

    def update_tokens(self, input_tokens: int | None, output_tokens: int | None):
        if input_tokens:
            self.total_input_tokens += input_tokens
        if output_tokens:
            self.total_output_tokens += output_tokens

    def context_usage_str(self) -> str:
        used = self.total_input_tokens + self.total_output_tokens
        if self.context_window <= 0:
            return f"ctx {used}"
        remaining = max(self.context_window - used, 0)
        return f"ctx {used}/{self.context_window} left {remaining}"

    def format_for_prompt(self) -> str:
        lines = ["## 🧭 SESSION CONTEXT"]
        if self.last_site:
            lines.append(f"- Last site: {self.last_site}")
        if self.last_url:
            lines.append(f"- Last URL: {self.last_url}")
        if self.last_title:
            lines.append(f"- Last page title: {self.last_title}")
        if self.last_app:
            lines.append(f"- Last app: {self.last_app}")
        if self.last_task:
            lines.append(f"- Last user task: {self.last_task}")
        return "\n".join(lines) if len(lines) > 1 else ""

    def resolve_task(self, task: str) -> str:
        """Add an explicit reference when the user uses ambiguous pronouns."""
        if not task:
            return task
        lower = task.lower()
        ambiguous = any(
            phrase in lower
            for phrase in [
                "in it",
                "there",
                "that tab",
                "this tab",
                "the tab",
                "that site",
                "this site",
                "the site",
            ]
        )
        if not ambiguous:
            return task

        target = self.last_site or self.last_url or self.last_app
        if not target:
            return task

        return f"{task}\n(Assume 'it/there/that tab' refers to {target}.)"

    def reference_hint(self, task: str) -> str:
        if not task:
            return ""
        lower = task.lower()
        ambiguous = any(
            phrase in lower
            for phrase in [
                "in it",
                "there",
                "that tab",
                "this tab",
                "the tab",
                "that site",
                "this site",
                "the site",
            ]
        )
        if not ambiguous:
            return ""
        if not (self.last_site or self.last_url or self.last_app):
            return ""
        lines = ["## 🔗 COREFERENCE HINT"]
        if self.last_site:
            lines.append(f"- If user says \"it/there/that tab\", assume {self.last_site}.")
        if self.last_url:
            lines.append(f"- Last URL: {self.last_url}")
        if self.last_app:
            lines.append(f"- Last app: {self.last_app}")
        return "\n".join(lines)


session_context = SessionContext()
