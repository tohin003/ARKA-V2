#!/usr/bin/env python3
"""
setup.py — ARKA V2 First-Time Setup Wizard

Interactive terminal setup for new users to configure API keys,
verify dependencies, and prepare the environment.

Run:  python setup.py
"""

import os
import sys
import shutil
import subprocess
import time

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.rule import Rule
    from rich.align import Align
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# ─── Fallback for when Rich isn't installed yet ──────────────────────
if not HAS_RICH:
    print("\n⚙️  Rich is not installed yet. Installing dependencies first...\n")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("\n✅ Dependencies installed. Restarting setup...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)

console = Console()

# ─── Colors ───────────────────────────────────────────────────────────
V = "#a78bfa"   # Violet
G = "#34d399"   # Green
M = "#6b7280"   # Muted
B = "#60a5fa"   # Blue
R = "#ef4444"   # Red
Y = "#fbbf24"   # Yellow


def print_logo():
    logo = f"""[bold {V}]
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
    console.print(logo)
    console.print()
    console.print(Align.center(Text("First-Time Setup", style=f"bold {G}")))
    console.print(Align.center(Text("Let's get ARKA running on your machine", style=M)))
    console.print()
    console.print(Rule(style=M))
    console.print()


def step_header(num, title):
    console.print(f"  [{V}]Step {num}[/]  [{B}]{title}[/]")
    console.print()


def check_python():
    """Step 1: Validate Python version."""
    step_header(1, "Python Environment")
    
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    
    if v.major == 3 and v.minor >= 10:
        console.print(f"  [{G}]✓[/] Python {version_str}")
        return True
    else:
        console.print(f"  [{R}]✕[/] Python {version_str} — ARKA requires Python 3.10+")
        console.print(f"    [{M}]Install from https://python.org/downloads[/]")
        return False


def install_deps():
    """Step 2: Install Python dependencies."""
    step_header(2, "Installing Dependencies")
    
    with Progress(
        SpinnerColumn(style=V),
        TextColumn(f"[{M}]Installing packages...[/]"),
        console=console,
    ) as progress:
        task = progress.add_task("install", total=None)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            capture_output=True, text=True
        )
    
    if result.returncode == 0:
        console.print(f"  [{G}]✓[/] All dependencies installed")
        return True
    else:
        console.print(f"  [{R}]✕[/] Installation failed:")
        console.print(f"    [{M}]{result.stderr[:200]}[/]")
        return False


def setup_playwright():
    """Install Playwright browsers if needed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            console.print(f"  [{G}]✓[/] Playwright browsers installed")
        else:
            console.print(f"  [{Y}]⚠[/] Playwright setup skipped (browser tools may not work)")
    except Exception:
        console.print(f"  [{Y}]⚠[/] Playwright setup skipped")


def configure_api_keys():
    """Step 3: Configure LLM provider API keys."""
    step_header(3, "API Key Configuration")
    
    console.print(f"  [{M}]ARKA needs at least one LLM provider to function.[/]")
    console.print(f"  [{M}]Keys are stored locally in .env (never committed to git).[/]")
    console.print()
    
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    existing = {}
    
    # Load existing keys
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    existing[key] = val.strip('"').strip("'")
    
    providers = [
        {
            "name": "OpenAI",
            "key": "OPENAI_API_KEY",
            "hint": "sk-proj-...",
            "url": "https://platform.openai.com/api-keys",
            "required": True,
        },
        {
            "name": "Anthropic",
            "key": "ANTHROPIC_API_KEY",
            "hint": "sk-ant-...",
            "url": "https://console.anthropic.com/settings/keys",
            "required": False,
        },
        {
            "name": "Google AI (Gemini)",
            "key": "GOOGLE_API_KEY",
            "hint": "AIza...",
            "url": "https://aistudio.google.com/app/apikey",
            "required": False,
        },
    ]
    
    # Observability (optional)
    obs_keys = [
        {"name": "Langfuse Secret Key", "key": "LANGFUSE_SECRET_KEY", "hint": "sk-lf-..."},
        {"name": "Langfuse Public Key", "key": "LANGFUSE_PUBLIC_KEY", "hint": "pk-lf-..."},
        {"name": "Langfuse Base URL",   "key": "LANGFUSE_BASE_URL",   "hint": "https://cloud.langfuse.com"},
    ]
    
    new_keys = dict(existing)
    
    # LLM Providers
    table = Table(show_header=True, header_style=f"bold {V}", box=None, padding=(0, 2))
    table.add_column("Provider", style=B)
    table.add_column("Status", justify="center")
    table.add_column("Required", justify="center")
    
    for p in providers:
        has_key = bool(existing.get(p["key"]))
        status = f"[{G}]✓ configured[/]" if has_key else f"[{M}]○ not set[/]"
        req = f"[{Y}]yes[/]" if p["required"] else f"[{M}]no[/]"
        table.add_row(p["name"], status, req)
    
    console.print(table)
    console.print()
    
    for p in providers:
        current = existing.get(p["key"], "")
        if current:
            masked = current[:8] + "..." + current[-4:] if len(current) > 12 else "****"
            change = Confirm.ask(f"  [{B}]{p['name']}[/] [{M}](current: {masked})[/] — Change?", default=False)
            if not change:
                continue
        else:
            if not p["required"]:
                skip = not Confirm.ask(f"  [{B}]{p['name']}[/] [{M}](optional)[/] — Configure?", default=False)
                if skip:
                    continue
        
        console.print(f"    [{M}]Get your key: {p['url']}[/]")
        key_val = Prompt.ask(f"    Enter {p['name']} API key", password=True)
        
        if key_val.strip():
            new_keys[p["key"]] = key_val.strip()
            console.print(f"    [{G}]✓[/] {p['name']} key saved")
        else:
            console.print(f"    [{Y}]⚠[/] Skipped")
    
    console.print()
    
    # Observability (optional)
    setup_obs = Confirm.ask(f"  [{B}]Configure Langfuse observability?[/] [{M}](optional)[/]", default=False)
    if setup_obs:
        for obs in obs_keys:
            current = existing.get(obs["key"], "")
            if current:
                console.print(f"    [{G}]✓[/] {obs['name']} already set")
            else:
                val = Prompt.ask(f"    {obs['name']} [{M}]({obs['hint']})[/]")
                if val.strip():
                    new_keys[obs["key"]] = val.strip()
    
    # Write .env
    with open(env_path, "w") as f:
        for k, v in new_keys.items():
            f.write(f'{k}="{v}"\n')
    
    console.print()
    console.print(f"  [{G}]✓[/] Configuration saved to .env")
    return bool(new_keys.get("OPENAI_API_KEY"))


def create_directories():
    """Step 4: Create required directories."""
    step_header(4, "Creating Directories")
    
    dirs = [
        os.path.expanduser("~/.arka"),
        os.path.expanduser("~/.arka/memory"),
        "logs",
        "memory",
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # Create learnings file if it doesn't exist
    learnings = "memory/learnings.md"
    if not os.path.exists(learnings):
        with open(learnings, "w") as f:
            f.write("# ARKA Learnings\n> Accumulated operational wisdom from past sessions.\n\n")
    
    # Create user profile if it doesn't exist
    profile = "memory/user_profile.md"
    if not os.path.exists(profile):
        with open(profile, "w") as f:
            f.write("# User Profile\n> ARKA's memory about you. Updated automatically.\n\n")
    
    console.print(f"  [{G}]✓[/] Directories and files ready")


def verify_setup():
    """Step 5: Quick verification."""
    step_header(5, "Verification")
    
    checks = []
    
    # Check .env exists
    checks.append(("Config file (.env)", os.path.exists(".env")))
    
    # Check critical imports
    try:
        import smolagents
        checks.append(("smolagents", True))
    except ImportError:
        checks.append(("smolagents", False))
    
    try:
        import rich
        checks.append(("rich", True))
    except ImportError:
        checks.append(("rich", False))
    
    try:
        import structlog
        checks.append(("structlog", True))
    except ImportError:
        checks.append(("structlog", False))
    
    try:
        import pyautogui
        checks.append(("pyautogui", True))
    except ImportError:
        checks.append(("pyautogui", False))
    
    try:
        from dotenv import load_dotenv
        checks.append(("python-dotenv", True))
    except ImportError:
        checks.append(("python-dotenv", False))
    
    all_ok = True
    for name, ok in checks:
        icon = f"[{G}]✓[/]" if ok else f"[{R}]✕[/]"
        console.print(f"  {icon} {name}")
        if not ok:
            all_ok = False
    
    return all_ok


def print_success():
    """Print final success screen."""
    console.print()
    console.print(Rule(style=G))
    console.print()
    
    success_panel = Panel(
        Align.center(Text.from_markup(
            f"[bold {G}]Setup Complete![/]\n\n"
            f"[{M}]Start ARKA with:[/]\n\n"
            f"[bold white]  python main.py[/]\n\n"
            f"[{M}]Or run tests first:[/]\n\n"
            f"[bold white]  python tests/test_phase6.py[/]"
        )),
        border_style=G,
        padding=(1, 4),
        title=f"[bold {G}]✓ Ready[/]",
        title_align="left",
    )
    console.print(success_panel)
    console.print()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    console.print()
    print_logo()
    
    # Step 1: Python
    if not check_python():
        console.print(f"\n  [{R}]Setup aborted. Please upgrade Python.[/]\n")
        sys.exit(1)
    console.print()
    
    # Step 2: Dependencies
    if not install_deps():
        console.print(f"\n  [{R}]Setup aborted. Fix dependency errors above.[/]\n")
        sys.exit(1)
    setup_playwright()
    console.print()
    
    # Step 3: API Keys
    has_key = configure_api_keys()
    if not has_key:
        console.print(f"\n  [{Y}]⚠ No OpenAI key configured. ARKA needs at least one LLM provider.[/]")
        console.print(f"  [{M}]You can add it later by editing .env[/]\n")
    console.print()
    
    # Step 4: Directories
    create_directories()
    console.print()
    
    # Step 5: Verify
    all_ok = verify_setup()
    console.print()
    
    if all_ok:
        print_success()
    else:
        console.print(f"  [{Y}]⚠ Some checks failed. ARKA may still work, but review errors above.[/]\n")


if __name__ == "__main__":
    main()
