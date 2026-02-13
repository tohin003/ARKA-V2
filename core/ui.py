"""
core/ui.py — ARKA V2 Terminal Interface

Premium, minimal terminal UI inspired by Claude Code's aesthetic.
Uses Rich for rendering with a dark, sophisticated color palette.
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme
from rich.table import Table
from rich.columns import Columns
from rich.rule import Rule
from rich.live import Live
from rich.spinner import Spinner
from rich.style import Style
from rich.align import Align
import datetime
import shutil
import sys
import threading
import select
import termios
import tty
from contextlib import contextmanager
from typing import Callable, List, Tuple

try:
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.styles import Style as PTStyle
    from prompt_toolkit.key_binding import KeyBindings
    PROMPT_TOOLKIT_AVAILABLE = True
except Exception:
    PROMPT_TOOLKIT_AVAILABLE = False


if PROMPT_TOOLKIT_AVAILABLE:
    PLAN_TEMPLATES: List[Tuple[str, str]] = [
        ("feature: ", "Plan a new feature"),
        ("bug: ", "Plan a bug fix"),
        ("refactor: ", "Plan a refactor"),
        ("test: ", "Plan test changes"),
        ("docs: ", "Plan documentation updates"),
        ("performance: ", "Plan performance work"),
        ("cleanup: ", "Plan cleanup/tech debt"),
    ]

    SUBCOMMANDS: dict[str, List[Tuple[str, str, str, bool]]] = {
        "memory": [
            ("list", "List recent facts", "/memory list [limit]", False),
            ("show", "Show a fact by ID", "/memory show <fact_id>", True),
            ("search", "Search facts", "/memory search <query> [--limit N]", True),
            ("stats", "Show memory counts", "/memory stats", False),
            ("forget", "Delete a fact by ID", "/memory forget <fact_id>", True),
            ("lock", "Lock a fact by ID", "/memory lock <fact_id>", True),
            ("export", "Export facts to JSON", "/memory export [path]", True),
            ("import", "Import facts from JSON", "/memory import <path>", True),
            ("purge", "Purge expired or old facts", "/memory purge [older_than_days]", True),
        ],
        "mcp": [
            ("list", "List MCP tools", "/mcp list", False),
            ("status", "Show MCP status", "/mcp status", False),
            ("tools", "List tools for a server", "/mcp tools <server_name>", True),
            ("call", "Call a tool", "/mcp call <tool_name> [arguments_json]", True),
            ("connect", "Connect a server", "/mcp connect <name> <command> [args...]", True),
            ("disconnect", "Disconnect all servers", "/mcp disconnect", False),
        ],
    }

    class SlashCommandCompleter(Completer):
        def __init__(self, get_items: Callable[[], List[Tuple[str, str]]]):
            self._get_items = get_items

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            if not text.startswith("/"):
                return

            if text.startswith("/plan "):
                partial = text[len("/plan "):]
                for tpl, desc in PLAN_TEMPLATES:
                    if tpl.startswith(partial):
                        yield Completion(
                            tpl,
                            start_position=-len(partial),
                            display=tpl,
                            display_meta=desc,
                        )
                return
            if text == "/plan":
                hint = f"templates: {', '.join(t[0].strip() for t in PLAN_TEMPLATES)}"
                yield Completion(
                    "/plan ",
                    start_position=-len(text),
                    display="/plan ",
                    display_meta=hint,
                )
                for tpl, desc in PLAN_TEMPLATES:
                    yield Completion(
                        f"/plan {tpl}",
                        start_position=-len(text),
                        display=f"/plan {tpl}",
                        display_meta=desc,
                    )
                return

            for base, subs in SUBCOMMANDS.items():
                prefix = f"/{base}"
                if text.startswith(prefix):
                    remainder = text[len(prefix):]
                    if remainder == "":
                        hint = f"subcommands: {', '.join(s[0] for s in subs)}"
                        yield Completion(
                            f"{prefix} ",
                            start_position=-len(text),
                            display=f"{prefix} ",
                            display_meta=hint,
                        )
                        for sub, _desc, usage, _needs_arg in subs:
                            yield Completion(
                                f"{prefix} {sub}",
                                start_position=-len(text),
                                display=f"{prefix} {sub}",
                                display_meta=usage,
                            )
                        return
                    if remainder.startswith(" "):
                        partial = remainder[1:]
                        if " " in partial:
                            return
                        for sub, _desc, usage, needs_arg in subs:
                            if sub.startswith(partial):
                                suffix = " " if needs_arg else ""
                                yield Completion(
                                    f"{sub}{suffix}",
                                    start_position=-len(partial),
                                    display=f"{prefix} {sub}{suffix}",
                                    display_meta=usage,
                                )
                        return

            if " " in text:
                return

            for cmd, desc in self._get_items():
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=cmd,
                        display_meta=desc,
                    )

class EscInterruptListener:
    def __init__(self, on_interrupt: Callable[[], None]):
        self._on_interrupt = on_interrupt
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._orig_term = None
        self._fd = None

    def start(self):
        if not sys.stdin.isatty():
            return
        try:
            self._fd = sys.stdin.fileno()
            self._orig_term = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        except Exception:
            return

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    ch = sys.stdin.read(1)
                    if ch == "\x1b":
                        self._on_interrupt()
            except Exception:
                return

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=0.2)
        if self._fd is not None and self._orig_term is not None:
            try:
                termios.tcsetattr(self._fd, termios.TCSADRAIN, self._orig_term)
            except Exception:
                pass

# ─── Theme ────────────────────────────────────────────────────────────
custom_theme = Theme({
    "arka.primary":    "bold #a78bfa",      # Soft violet
    "arka.secondary":  "#818cf8",            # Indigo
    "arka.accent":     "#34d399",            # Emerald green
    "arka.muted":      "#6b7280",            # Gray-500
    "arka.dim":        "dim #9ca3af",        # Gray-400
    "arka.error":      "bold #ef4444",       # Red
    "arka.warning":    "#f59e0b",            # Amber
    "arka.success":    "bold #10b981",       # Green
    "arka.info":       "#60a5fa",            # Blue
    "arka.user":       "bold #e0e7ff",       # Light indigo
    "arka.tool":       "#fbbf24",            # Yellow
    "arka.border":     "#4f46e5",            # Indigo-600
})

console = Console(theme=custom_theme)

# ─── Constants ────────────────────────────────────────────────────────
VERSION = "2.0.6"
LOGO = """[bold #a78bfa]
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║     █████╗ ██████╗ ██╗  ██╗ █████╗    ║
    ║    ██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗   ║
    ║    ███████║██████╔╝█████╔╝ ███████║   ║
    ║    ██╔══██║██╔══██╗██╔═██╗ ██╔══██║   ║
    ║    ██║  ██║██║  ██║██║  ██╗██║  ██║   ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ║
    ║                                       ║
    ╚═══════════════════════════════════════╝[/]"""


class ArkaUI:
    """Premium terminal interface for ARKA V2."""

    def __init__(self):
        self.console = console
        self.term_width = min(shutil.get_terminal_size().columns, 100)

    # ─── Welcome Screen ───────────────────────────────────────────────

    def print_welcome(self):
        """Print the premium startup screen."""
        self.console.print()
        self.console.print(LOGO)
        self.console.print()

        # Status bar
        now = datetime.datetime.now().strftime("%I:%M %p")
        info_table = Table.grid(padding=(0, 3))
        info_table.add_row(
            Text(f"v{VERSION}", style="arka.muted"),
            Text("│", style="arka.muted"),
            Text("God Mode Agent", style="arka.secondary"),
            Text("│", style="arka.muted"),
            Text(now, style="arka.muted"),
        )
        self.console.print(Align.center(info_table))
        self.console.print()

        # Quick help
        help_items = [
            ("Type", "a message to chat"),
            ("/help", "list commands"),
            ("exit", "quit"),
        ]
        help_parts = []
        for key, desc in help_items:
            help_parts.append(f"[arka.accent]{key}[/] [arka.dim]{desc}[/]")
        self.console.print(Align.center(Text.from_markup("  •  ".join(help_parts))))

        self.console.print()
        self.console.print(Rule(style="arka.muted"))
        self.console.print()

    # ─── User Input ───────────────────────────────────────────────────

    def get_input(self) -> str:
        """Get user input with styled prompt."""
        try:
            if PROMPT_TOOLKIT_AVAILABLE and sys.stdin.isatty() and sys.stdout.isatty():
                return self._get_input_prompt_toolkit()
            return self.console.input("[arka.accent]❯[/] ")
        except EOFError:
            return "exit"
        except Exception:
            return self.console.input("[arka.accent]❯[/] ")

    def _get_input_prompt_toolkit(self) -> str:
        from core.skills import skill_registry

        completer = SlashCommandCompleter(skill_registry.get_completion_items)
        key_bindings = KeyBindings()

        @key_bindings.add("escape")
        def _(event):
            event.app.exit(result="")

        @key_bindings.add("backspace")
        def _(event):
            event.app.current_buffer.delete_before_cursor(1)
            event.app.current_buffer.start_completion(select_first=False)

        @key_bindings.add("c-h")
        def _(event):
            event.app.current_buffer.delete_before_cursor(1)
            event.app.current_buffer.start_completion(select_first=False)

        prompt_style = PTStyle.from_dict({
            "prompt": "ansigreen bold",
            "completion-menu.completion": "bg:#1f2937 #e5e7eb",
            "completion-menu.completion.current": "bg:#34d399 #111827",
            "completion-menu.meta": "bg:#1f2937 #9ca3af",
            "completion-menu.meta.current": "bg:#34d399 #111827",
        })

        return pt_prompt(
            ANSI("\x1b[32m❯\x1b[0m "),
            completer=completer,
            complete_while_typing=True,
            key_bindings=key_bindings,
            style=prompt_style,
        )

    @contextmanager
    def esc_interrupt_listener(self, on_interrupt: Callable[[], None]):
        listener = EscInterruptListener(on_interrupt)
        listener.start()
        try:
            yield
        finally:
            listener.stop()

    # ─── Agent Output ─────────────────────────────────────────────────

    def print_thought(self, text: str):
        """Show agent's internal thinking."""
        if not text:
            return
        self.console.print(f"  [arka.dim]⟡ {text}[/]")

    def print_tool_call(self, tool_name: str, args: str = ""):
        """Show a tool being called."""
        self.console.print(f"  [arka.tool]⚡ {tool_name}[/][arka.dim]({args})[/]")

    def print_tool_result(self, result: str):
        """Show tool execution result."""
        display = result[:400] + "…" if len(result) > 400 else result
        self.console.print(f"  [arka.dim]  ↳ {display}[/]")

    def print_step(self, step_number: int, summary: str, context: str | None = None):
        """Show a concise step summary (CLI-style)."""
        suffix = f" [{context}]" if context else ""
        self.console.print(f"  [arka.dim]• Step {step_number}: {summary}{suffix}[/]")

    def print_success(self, message: str):
        """Show final answer in a clean panel."""
        self.console.print()
        self.console.print(Panel(
            Markdown(str(message)),
            border_style="arka.accent",
            padding=(1, 2),
            title="[arka.accent]arka[/]",
            title_align="left",
            subtitle=f"[arka.dim]{datetime.datetime.now().strftime('%H:%M:%S')}[/]",
            subtitle_align="right",
        ))

    def print_error(self, message: str):
        """Show error message."""
        self.console.print(f"\n  [arka.error]✕ {message}[/]\n")

    def print_warning(self, message: str):
        """Show warning message."""
        self.console.print(f"  [arka.warning]⚠ {message}[/]")

    def print_info(self, message: str):
        """Show info message."""
        self.console.print(f"  [arka.info]ℹ {message}[/]")

    def print_user_msg(self, msg: str):
        """Echo user message (if needed)."""
        self.console.print(f"  [arka.user]{msg}[/]")

    def spinner(self, text: str = "Thinking"):
        """Context manager for loading spinner."""
        return self.console.status(
            f"[arka.secondary]  {text}...[/]",
            spinner="dots",
            spinner_style="arka.primary"
        )

    def print_divider(self):
        """Print a subtle divider."""
        self.console.print(Rule(style="arka.muted"))

    def print_system(self, message: str):
        """Print a system-level message."""
        self.console.print(f"  [arka.muted]│ {message}[/]")

    def print_context(self, message: str):
        """Print context usage (compact, persistent indicator)."""
        if message:
            self.console.print(f"  [arka.dim]{message}[/]")

    def print_goodbye(self):
        """Print exit message."""
        self.console.print()
        self.console.print(f"  [arka.dim]Session ended. Goodbye.[/]")
        self.console.print()


# Singleton
ui = ArkaUI()
