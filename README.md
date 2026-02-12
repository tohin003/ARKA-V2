<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/macOS-Only-black?logo=apple&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Tools-40%2B-purple" />
  <img src="https://img.shields.io/badge/Phase-7%20Complete-gold" />
</p>

<h1 align="center">
  <br>
  ARKA V2 — The God Mode Agent
  <br>
</h1>

<p align="center">
  <b>A local AI agent that controls your entire Mac — with memory, vision, emotional intelligence, and infinite extensibility.</b>
</p>

<p align="center">
  <code>OpenClaw's Soul</code> + <code>Claude Code's Hands</code> + <code>Antigravity's Brain</code>
</p>

---

## What is ARKA?

ARKA is a **local, proactive AI agent** that runs in your terminal and has full control over your macOS system. It can play music, send WhatsApp messages, browse the web, write code, manage your todos, control hardware — and it **remembers you** across sessions.

Unlike cloud-based assistants, ARKA runs entirely on your machine. It sees your screen, knows what app you're using, adapts to your mood, learns from its mistakes, and pursues multi-step goals autonomously.

```
❯ Send hello to Mom on WhatsApp
  ⟡ Processing
  ⚡ send_whatsapp_message(contact_name="Mom", message="hello")
╭─ arka ────────────────────────────────── 10:30:15 ─╮
│  Message sent to 'Mom' (Strictly Verified).         │
╰────────────────────────────────────────────────────╯
```

---

## Inspiration — The DNA

ARKA is a hybrid of three paradigms:

| Origin | What ARKA Inherits | Implementation |
|:---|:---|:---|
| **[OpenClaw](https://github.com/AiOClaw)** | Persistent memory, proactive heartbeat, pattern learning, self-reflection | `user_profile.md`, `learnings.md`, `HeartbeatScheduler`, `PatternLearner`, `ReflectionEngine` |
| **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** | OS-level tool execution, safety guards, structured code generation | `CodeAgent`, `MistakeGuard`, 40+ tools, `pyautogui` + AppleScript |
| **[Antigravity](https://deepmind.google)** | Context sensing, adaptive communication, goal persistence | `ContextSensor`, `ToneAdapter`, `GoalManager` |

---

## Features

### 🛠️ 40+ Built-in Tools (Phase 7)

<table>
<tr>
<td width="50%">

**System Control**
- `system_click` — Vision-guided UI clicking (PyAutoGUI)
- `system_type` — Type into any field
- `open_app` — Launch apps (or open URLs via an app)

**Hardware**
- `music_control` — Apple Music (play/pause/next)
- `set_volume` — System volume (0-100)
- `wifi_control` — WiFi on/off
- `bluetooth_control` — Bluetooth on/off

**Communication**
- `send_whatsapp_message` — Vision-verified messaging
- `visit_page` — Headless browsing (Playwright)

</td>
<td width="50%">

**Productivity**
- `todo_add` / `todo_list` / `todo_complete` — Task manager
- `set_goal` / `list_goals` / `advance_goal` / `complete_goal` — Multi-step goals
- `remember_fact` — Save facts to memory
- `web_search` — DuckDuckGo search

**Developer**
- `generate_graph` — Codebase dependency graph

**Browser (Chrome DOM Control — requires extension)**
- `chrome_navigate` / `chrome_click` / `chrome_type` / `chrome_scroll`
- `chrome_wait_for_selector` / `chrome_get_text` / `chrome_get_dom` / `chrome_get_elements`
- `chrome_list_tabs` / `chrome_new_tab` / `chrome_switch_tab`
- `chrome_status` / `chrome_wait_for_connection` / `chrome_continue`

**Extensibility**
- `list_mcp_tools` — Discover MCP server tools
- `call_mcp_tool` — Use any MCP tool
- `get_screen_coordinates` — Vision AI targeting

</td>
</tr>
</table>

### 🧠 Memory System (The Cortex)

ARKA has three layers of persistent memory:

```
┌─────────────────────────────────────┐
│  user_profile.md                    │  ← Who you are (name, preferences)
│  learnings.md                       │  ← What ARKA has learned 
│  session_history.db (SQLite)        │  ← Full conversation history
└─────────────────────────────────────┘
```

- **Semantic Memory**: Facts saved via `remember_fact` → `user_profile.md`
- **Operational Memory**: Post-session reflections → `learnings.md`  
- **Session History**: Every event logged to SQLite with timestamps

### 💓 Proactive Heartbeat

ARKA doesn't just wait for commands — it has a background daemon:

| Job | Schedule | What It Does |
|:---|:---|:---|
| Pulse | Every 5 min | Health check |
| Pattern Learning | Every 30 min | Analyzes your usage patterns |
| Morning Briefing | 9:00 AM | Daily summary |
| Evening Review | 9:00 PM | Session wrap-up |

### 🎯 Multi-Step Goals

Set high-level goals and ARKA tracks them across sessions:

```
❯ Set a goal to deploy my app with steps: write tests, fix bugs, deploy
  ╭─ arka ─────────────────────────────────────╮
  │  🎯 Goal 'Deploy my app' created (3 steps) │
  ╰────────────────────────────────────────────╯

❯ What are my goals?
  🎯 [a1b2] Deploy my app (1/3)
     ✅ 1. Write tests
     ⬜ 2. Fix bugs        ← NEXT
     ⬜ 3. Deploy
```

### 🖥️ Context Awareness

ARKA knows what you're doing right now via AppleScript:

```
## 🖥️ CURRENT CONTEXT
- Active App: Visual Studio Code
- Window: engine.py — ARKA-V2
```

This is injected into every prompt so ARKA can tailor responses to your current activity.

### 🎭 Adaptive Communication

ARKA detects your tone and adapts:

| Your Message | ARKA's Tone | Response Style |
|:---|:---|:---|
| `FIX THIS NOW!!!` | URGENT | One-line answer, skip explanations |
| `Why doesn't this work?` | FRUSTRATED | Acknowledge → fix |
| `Hey what's up?` | CASUAL | Warm and friendly |
| `Could you please explain...` | DETAILED | Thorough, structured |
| `ok` | TERSE | Match energy, concise |

### 🔌 MCP Integration (Infinite Tools)

Connect ARKA to any MCP-compatible server:

```python
# ARKA can discover and use tools from any MCP server
❯ List MCP tools from the filesystem server
  ⚡ list_mcp_tools(server_command="npx", server_args="@modelcontextprotocol/server-filesystem /tmp")
  → Available: read_file, write_file, list_directory, ...
```

### 👁️ Vision System

ARKA can see your screen via GPT-5.2 Vision and click precisely:

```
❯ Click the Send button
  ⟡ Processing
  ⚡ get_screen_coordinates("Send button")    → (842, 651)
  ⚡ system_click at (842, 651)
```

### 🛡️ Safety Guards

| Guard | What It Blocks |
|:---|:---|
| `MistakeGuard` | `rm -rf /`, `sudo`, fork bombs, `shutdown` |
| `pyautogui.FAILSAFE` | Move mouse to corner to abort |
| Token limits | Prevents runaway LLM costs |
| Vision verification | WhatsApp messages verified before sending |
| Strict output verification | Downgrades unverified “success” claims unless DOM checks confirm |

---

## Architecture

```
┌───────────────────────────────────────────────────┐
│                    main.py                         │
│              ┌──────────────┐                      │
│              │   ArkaUI     │ ← Premium terminal   │
│              └──────┬───────┘                      │
│                     │                              │
│              ┌──────▼───────┐                      │
│              │  ArkaEngine  │ ← CodeAgent + 40+    │
│              │              │   tools               │
│              └──────┬───────┘                      │
│                     │                              │
│    ┌────────────────┼────────────────┐             │
│    │                │                │             │
│    ▼                ▼                ▼             │
│ ┌──────┐     ┌───────────┐    ┌──────────┐        │
│ │Memory│     │   Tools   │    │   Core   │        │
│ ├──────┤     ├───────────┤    ├──────────┤        │
│ │db.py │     │hardware.py│    │llm.py    │        │
│ │memory│     │system.py  │    │scheduler │        │
│ │  .py │     │browser.py │    │mcp_client│        │
│ │mistak│     │messaging  │    │pattern   │        │
│ │es.py │     │todo.py    │    │ learner  │        │
│ │      │     │vision.py  │    │reflection│        │
│ │      │     │search.py  │    │context   │        │
│ │      │     │goal_tools │    │ sensor   │        │
│ │      │     │mcp_tools  │    │tone      │        │
│ │      │     │memory_tool│    │ adapter  │        │
│ └──────┘     └───────────┘    └──────────┘        │
│                                                    │
│              ┌───────────────┐                     │
│              │  Observability│                     │
│              │  (Langfuse)   │                     │
│              └───────────────┘                     │
└───────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    │
    ├─► Context Sensor (AppleScript → active app)
    ├─► Tone Adapter (message analysis → directive)
    │
    ▼
ArkaEngine.run()
    │
    ├─► MistakeGuard (safety check)
    ├─► Augmented prompt = context + tone + user input
    ├─► System prompt includes:
    │     • Rules & personality
    │     • Semantic memory (user_profile.md)
    │     • Operational learnings (learnings.md)
    │     • Active goals
    │
    ▼
CodeAgent (smolagents)
    │
    ├─► Generates Python code
    ├─► Calls tools (music, system, browser, etc.)
    ├─► Returns final answer
    │
    ▼
Post-Execution
    ├─► Log to SQLite
    ├─► Reflect on errors (→ learnings.md)
    └─► Display in paneled UI
```

### File Structure

```
ARKA-V2/
├── main.py                    # Entry point
├── setup.py                   # First-time setup wizard
├── requirements.txt           # Python dependencies
├── .env                       # API keys (gitignored)
├── implementation_plan.md     # Planning-mode output (updated by `plan`)
├── ultimate_plan.md           # Long-form roadmap/notes
│
├── core/                      # Brain
│   ├── engine.py              # ArkaEngine (CodeAgent + tools)
│   ├── llm.py                 # ModelRouter (LLM provider)
│   ├── responses_model.py      # OpenAI Responses API wrapper
│   ├── ui.py                  # Premium terminal UI
│   ├── scheduler.py           # Heartbeat daemon
│   ├── skills.py              # Slash commands (/help, /status)
│   ├── memory.py              # Semantic memory manager
│   ├── mcp_client.py          # MCP Bridge (async→sync)
│   ├── pattern_learner.py     # Phase 6.1 — Usage pattern mining
│   ├── goal_manager.py        # Phase 6.2 — Multi-step goals
│   ├── reflection.py          # Phase 6.3 — Self-improvement
│   ├── context_sensor.py      # Phase 6.4 — Desktop awareness
│   ├── tone_adapter.py        # Phase 6.5 — Emotion detection
│   ├── vision_client.py       # GPT Vision integration
│   ├── session_context.py      # Short-term session state + coreference hints
│   ├── verification.py         # Post-run verification + success-claim guardrails
│   ├── browser_bridge.py       # Phase 7 — WebSocket server for Chrome extension
│   └── hooks.py               # Event hooks
│
├── tools/                     # Hands
│   ├── hardware.py            # Music, volume, WiFi, Bluetooth
│   ├── system.py              # Click, type, hotkey, open app
│   ├── messaging.py           # WhatsApp (vision-verified)
│   ├── browser.py             # Playwright web browsing
│   ├── chrome_tools.py         # Phase 7 — Chrome DOM tools via extension bridge
│   ├── vision.py              # Screen coordinate detection
│   ├── search.py              # DuckDuckGo search
│   ├── todo.py                # Task management
│   ├── goal_tools.py          # Goal CRUD tools
│   ├── memory_tools.py        # remember_fact tool
│   ├── mcp_tools.py           # MCP discovery + calling
│   ├── codebase_graph.py      # Code dependency visualization
│   ├── dev.py                 # Developer utilities
│   ├── git.py                 # Git operations
│   └── terminal.py            # Shell command execution
│
├── extension/                 # Phase 7 — Chrome extension (load unpacked)
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
│
├── claude-code-system-prompts/ # Vendored prompts/tools reference
│   └── ...
│
├── scripts/                   # Helper scripts
│   ├── setup.py               # Installs common macOS deps (Homebrew)
│   └── check_models.py         # Lists available OpenAI models
│
├── memory/                    # Long-term storage
│   ├── db.py                  # SQLite session history
│   ├── mistakes.py            # Safety guard patterns
│   ├── user_profile.md        # Known facts about user
│   └── learnings.md           # Accumulated wisdom
│
├── observability/             # Monitoring
│   └── logger.py              # Langfuse integration
│
├── tests/                     # Verification
│   ├── test_phase6.py         # All Phase 6 tests (23 checks)
│   ├── test_full_integration.py # Full integration (22 checks)
│   └── ...
│
└── logs/                      # Runtime logs
    └── arka.jsonl
```

---

## Quick Start

### Prerequisites

- **macOS** (ARKA uses AppleScript, pyautogui, and macOS-specific APIs)
- **Python 3.10+** (Python 3.12 recommended; some PyAutoGUI dependencies may break on Python 3.13)
- **OpenAI API key** (GPT-5.2 for reasoning and vision)

### Installation

```bash
# 1. Clone
git clone https://github.com/tohin003/ARKA-V2.git
cd ARKA-V2

# 2. Run setup wizard (installs deps + configures API keys)
python setup.py

# 3. Launch ARKA
python main.py
```

### (Optional) Enable Chrome DOM Control (Phase 7)

ARKA supports **precise, DOM-level web automation** in Google Chrome via a local WebSocket bridge + bundled extension (`tools/chrome_tools.py`).

1) Install the extension:
- Open `chrome://extensions`
- Enable **Developer mode**
- Click **Load unpacked** → select `extension/`

2) Run ARKA:
- `python main.py`
- You should see: `Browser Bridge active (ws://127.0.0.1:7777)` (host/port configurable)

3) Use it:
- Ask ARKA to use Chrome, e.g. “Open Chrome and go to github.com”
- If ARKA pauses for login, log in manually, then tell ARKA “continue” (it will call `chrome_continue`)

### Manual Setup (Alternative)

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web browsing)
python -m playwright install chromium

# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY="your-key-here"
# Optional:
# ANTHROPIC_API_KEY="sk-ant-..."
# GOOGLE_API_KEY="AIza..."
# LANGFUSE_SECRET_KEY="sk-lf-..."
# LANGFUSE_PUBLIC_KEY="pk-lf-..."
# LANGFUSE_BASE_URL="https://cloud.langfuse.com"
EOF

# Run
python main.py
```

### System Dependencies (Optional, macOS)

- `bluetooth_control` requires `blueutil` (install via Homebrew): `brew install blueutil`
- There is a helper: `python scripts/setup.py` (checks Homebrew + installs common packages)

### macOS Permissions

ARKA needs these permissions (System Settings → Privacy & Security):

| Permission | Why | How to Grant |
|:---|:---|:---|
| **Accessibility** | Screen clicking, typing | Settings → Accessibility → Terminal ✓ |
| **Screen Recording** | Vision (screenshots) | Settings → Screen Recording → Terminal ✓ |
| **Automation** | AppleScript (Music, WhatsApp) | Auto-prompted on first use |

---

## Usage

### Basic Commands

```bash
❯ Play Breakup Party               # Controls Apple Music
❯ Set volume to 50                  # System volume
❯ Send hello to Mom on WhatsApp     # Vision-verified messaging
❯ Search for Python decorators      # Web search
❯ Open Safari                       # Launch apps
❯ What are my todos?                # Task management
```

### Slash Commands

```bash
❯ /help                             # List all commands
❯ /status                           # Git status
❯ /commit Fixed the login bug       # Git commit
```

### Planning Mode

```bash
❯ plan Add a /status command that also shows branch name
```

- Planning mode updates `implementation_plan.md` and does **not** execute changes.

### Goals

```bash
❯ Set a goal to learn Rust with steps: install rustc, write hello world, build a CLI
❯ What are my goals?
❯ Advance goal a1b2
```

### Memory

```bash
❯ Remember that my name is Alex
❯ Remember that I prefer dark mode
❯ What do you know about me?
```

### Exit

```bash
❯ exit                              # Graceful shutdown with reflection
❯ quit                              # Same
❯ q                                 # Same
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|:---|:---|:---|
| `OPENAI_API_KEY` | ✅ | Primary LLM (GPT-5.2) |
| `ANTHROPIC_API_KEY` | Optional | Present in setup wizard (not currently used by core runtime) |
| `GOOGLE_API_KEY` | Optional | Present in setup wizard (not currently used by core runtime) |
| `LANGFUSE_SECRET_KEY` | Optional | Observability |
| `LANGFUSE_PUBLIC_KEY` | Optional | Observability |
| `LANGFUSE_BASE_URL` | Optional | Observability |
| `ARKA_PLANNER_MODEL` | Optional | Planner model ID (Responses API) |
| `ARKA_EXECUTOR_MODEL` | Optional | Executor model ID (chat) |
| `ARKA_VISION_MODEL` | Optional | Vision model ID |
| `ARKA_ROUTER_MODEL` | Optional | Router model ID (Responses API) |
| `ARKA_VERIFIER_MODEL` | Optional | Verifier model ID (Responses API) |
| `ARKA_CONTEXT_WINDOW` | Optional | Context window accounting (default `128000`) |
| `ARKA_BRIDGE_HOST` | Optional | Browser Bridge host (default `127.0.0.1`) |
| `ARKA_BRIDGE_PORT` | Optional | Browser Bridge port (default `7777`) |

### Changing the LLM Model

Prefer `.env` overrides (see `core/llm.py`):

```dotenv
ARKA_EXECUTOR_MODEL="gpt-5.2-chat-latest"
ARKA_PLANNER_MODEL="gpt-5.2-pro-2025-12-11"
ARKA_ROUTER_MODEL="gpt-5.1-2025-11-13"
ARKA_VERIFIER_MODEL="gpt-5.2-pro-2025-12-11"
ARKA_VISION_MODEL="gpt-4o-2024-11-20"
```

---

## Running Tests

```bash
# Phase 6 tests (23 checks — AGI capabilities)
python tests/test_phase6.py

# Phase 7 tests (Chrome extension + bridge)
python tests/test_phase7.py

# Full integration (22 checks — all subsystems)
python tests/test_full_integration.py

# Run the full test suite
python tests/run_all_tests.py

# Individual module tests
python tests/test_memory.py
python tests/test_heartbeat.py
python tests/test_mcp.py
```

---

## Development Phases

| Phase | Status | Description |
|:---|:---|:---|
| 1 | ✅ | Core engine + ModelRouter |
| 2 | ✅ | God Mode tools (system, hardware, vision) |
| 3 | ✅ | Safety (MistakeGuard + observability) |
| 4 | ✅ | Skills, Planner, Session DB |
| 5.1 | ✅ | Semantic Memory (The Cortex) |
| 5.2 | ✅ | Heartbeat (Proactivity) |
| 5.3 | ✅ | MCP Integration (Infinite Tools) |
| **6.1** | ✅ | **Pattern Learning (The Subconscious)** |
| **6.2** | ✅ | **Goal Persistence (Multi-Step Autonomy)** |
| **6.3** | ✅ | **Reflection Loop (Self-Improvement)** |
| **6.4** | ✅ | **Context Sensing (Situational Awareness)** |
| **6.5** | ✅ | **Adaptive Communication (EQ)** |
| **7** | ✅ | **Browser Bridge (Chrome extension + DOM automation)** |

---

## Tech Stack

| Component | Technology |
|:---|:---|
| Agent Framework | [smolagents](https://github.com/huggingface/smolagents) (HuggingFace) |
| LLM | OpenAI GPT-5.2 (configurable) |
| Vision | GPT-5.2 Vision API |
| Terminal UI | [Rich](https://github.com/Textualize/rich) |
| OS Control | PyAutoGUI + AppleScript |
| Browser | Playwright (Chromium) |
| Browser Bridge | `websockets` + Chrome Extension (Manifest V3) |
| Database | SQLite3 |
| Tool Protocol | [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) |
| Observability | [Langfuse](https://langfuse.com/) |
| Scheduling | Python `schedule` + `threading` |

---

## License

MIT

---

<p align="center">
  <b>Built with 🧬 by combining the best ideas from OpenClaw, Claude Code, and Antigravity</b>
</p>
