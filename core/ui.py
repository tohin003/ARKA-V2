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
            return self.console.input("[arka.accent]❯[/] ")
        except EOFError:
            return "exit"

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
