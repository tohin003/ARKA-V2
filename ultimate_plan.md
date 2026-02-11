# ARKA v2: The Ultimate Super Agent Master Plan

> **Status:** Phase 0 (Ready to Start)
> **Version:** 4.1 (God Tier + Claude Code Features)
> **Last Updated:** Jan 31, 2026

---

## 1. Project Vision
**Goal:** Build a CLI-based AI Agent that:
1.  **Rivals Claude Code** in coding capability (streaming UI, context awareness).
2.  **Exceeds Claude Code** with "God Mode" (Full OS Control via Vision + Mouse/Keyboard).
3.  **Self-Corrects** using a dedicated "Mistake Guard" memory.

---

## 2. The "God Tier" Intelligence Stack
We utilize the absolute bleeding edge models available in your API key (`sk-proj...`).

| Component | Model | Role & Capability |
| :--- | :--- | :--- |
| **The Planner** | `gpt-5.2-pro` | **"The Brain"**. Handles high-level reasoning, detailed planning, and debugging logic. <br> *Key Feature: 256k Context, Hallucination Resistance.* |
| **The Executor** | `gpt-5.2-codex` | **"The Hands"**. Specifically fine-tuned for Agentic Coding, Security, and Tool Use. <br> *Key Feature: 80% SWE-Bench Verified score.* |
| **The Eyes** | `gpt-5.2-pro` | **"Vision"**. Analyzes screenshots to return X,Y coordinates for clicks. <br> *Key Feature: 2x better UI element recognition.* |

---

## 3. Architecture & Framework

### A. Core Engine (`smolagents`)
*   **Philosophy:** "Code as Action". The agent interacts with the world by writing and executing Python scripts in a local sandbox.
*   **Base Class:** `CodeAgent` (subclassed to add our specific Hooks and Memory interops).
*   **Interpreter:** `LocalPythonInterpreter` configured to allow safe imports (`pyautogui`, `playwright`).

### B. Memory Strategy (The "Best of Both" Architecture)
We combine the simplicity of Claude's static memory with the robustness of V1's dynamic memory.

| Layer | Implementation | Purpose |
| :--- | :--- | :--- |
| **Static Context** | `ARKA.md` | **Project Rules.** A Markdown file in the project root (e.g., "Always use async"). Loaded into System Prompt. <br> *Source: Claude Code inspired.* |
| **Session History** | `sqlite` | **Conversation Log.** Stores every message, tool call, and result in `~/.arka/memory/session_history.db`. SQL allows complex context queries. |
| **Mistake Guard** | `mistakes.json` | **Active Defense.** A vector/keyword store of past failures. <br> *Logic:* Before acting, check if plan matches a known failure pattern. If so, ABORT and warn. |

### C. UI/UX (The Claude Code Replica)
We use the `rich` library to replicate the premium CLI experience.
*   **Streaming Markdown:** Real-time token streaming with syntax highlighting.
*   **"Thinking..." Panels:** Collapsible gray panels showing the Planner's internal reasoning (chains of thought) before the final output.
*   **Tool Panels:** Boxed inputs/outputs for tools (e.g., Terminal, Browser) with Success/Fail icons (✅/❌).
*   **Status Footer:** Persistent display of "Tokens Used" and "Session Cost ($)".

---

## 4. The Toolbox ("God Mode")

All tools are Python functions decorated with `@tool` and exposed to `gpt-5.2-codex`.

### A. System Control (The "God Mode" Differentiator)
*   **Vision Control:** `system_click(query)`: Screenshot -> GPT-5.2 -> Coords -> Click.
*   **Media Control:** `music(action)`: `osascript` wrapper for Apple Music (Play/Pause/Next/Vol).
*   **Hardware Control:** 
    *   `wifi(status)` using `networksetup`.
    *   `bluetooth(status)` using `blueutil`.
    *   `volume(level)` using `osascript`.
*   **Safety:** `pyautogui.failsafe = True` (Mouse to corner kills the agent).

### B. Developer Tools (Standard)
*   `read_file(path, line_numbers=True)`: Intelligent file reading.
*   `write_file(path, content)`: Atomic writes.
*   `run_terminal(command)`: Captures `stdout` + `stderr`.
*   `grep(pattern, path)`: Recursive search.

### C. Browser Tools (Playwright)
*   `browser_visit(url)`: Persistent context (keeps cookies).
*   `browser_scrape()`: Returns simplified Markdown for LLM reading.

---

## 5. Master Implementation Roadmap (Phased)

We follow a strict "Additive" philosophy. Phase 0 provides the stable core. Future phases add capabilities without breaking the foundation.

### Phase 0: Foundation & Observability
**Goal:** A stable, logging-enabled CLI that can run basic Python code.
1.  **Setup:** Git, Venv, Structure (`core`, `tools`, `memory`).
2.  **Observability:** `structlog` (JSON logs) + `Langfuse` (Tracing).
3.  **Core:** `ModelRouter` (Adapter for 5.2 models) + `CodeAgent` engine.

### Phase 1: The Engine (Text Tools)
**Goal:** Parity with basic coding agents.
1.  Implement `DevToolbox` (File I/O, Terminal, Grep).
2.  verify `gpt-5.2-codex` can write/run code loops.

### Phase 2: "God Mode" (System Tools)
**Goal:** OS Interaction.
1.  Implement `SystemToolbox` (Vision + PyAutoGUI).
2.  Implement `failsafe` mechanisms.

### Phase 3: The Brain (Memory & Logic)
**Goal:** Long-term persistence.
1.  Implement `MemoryClient`: `ARKA.md` loader + `SQLite` storage.
2.  Implement `MistakeGuard`: The "Pre-flight check" hook.

### Phase 4: UI/UX & Polish
**Goal:** The "Claude Code" Experience.
1.  Implement `rich` UI renderer (Streaming, Spinners).
2.  Add Slash Commands (`/clear`, `/cost`, `/compact`).

---

## 6. Compatibility & Failure Handling

### Compatibility Strategy
*   **Tool Agnosticism:** The Core Engine doesn't know *what* tools it has, only *that* it has tools. We can swap `SystemToolbox` for `SafeToolbox` without code changes.
*   **Regression Testing:** Each Phase ends with a standard "Hello World" test to ensure previous features still work.

### Failure Handling Strategy
*   **Tool Level:** Tools catch exceptions and return informative strings (e.g., "Error: File not found") instead of crashing.
*   **Logic Level:** If a tool fails, the LLM is prompted to "Reason about the error and retry with a different approach."
*   **System Level:** Hard crash logs are saved to `crash.log` for post-mortem.

---

## 7. File Structure
```
/Users/xyx/Documents/DESKTOP/AGENT/AI_AGENT-V2/
├── ARKA.md                 # Static Project Rules (User Editable)
├── main.py                 # CLI Entry Point
├── core/
│   ├── engine.py           # Smolagents CodeAgent Subclass
│   ├── llm.py              # Model Adapters (GPT-5.2)
│   ├── ui.py               # Rich UI Renderer
│   └── hooks.py            # Pre/Post execution hooks
├── tools/
│   ├── dev.py              # File/Terminal Tools
│   ├── system.py           # Vision/OS Tools
│   └── browser.py          # Playwright Tools
├── memory/
│   ├── db.py               # SQLite Client
│   └── mistakes.py         # MistakeGuard Logic
└── observability/
    └── logger.py           # Structlog & Langfuse
```

---

## 9. Capabilities Matrix: Claude Code vs. Antigravity V2

The following table compares the analyzed features of Claude Code against our implementation plan for Antigravity V2.

| Feature Area | Claude Code Feature (Researched) | Antigravity V2 Implementation (God Tier) | Status |
| :--- | :--- | :--- | :--- |
| **Workflow** | **Plan Mode:** Iterative loop (Explore -> Interview -> Draft) before execution. | **Plan Mode:** Implementing exact replica in `core/modes/planning.py` with `task.md` integration. | ✅ Planned |
| **Task Mgmt** | **Todo List:** `/todo` tool for tracking multi-step progress in real-time. | **TodoTool:** `tools/todo.py` with `rich` panel rendering and strict single-task focus. | ✅ Planned |
| **Memory** | **CLAUDE.md:** Static project rules file. | **ARKA.md:** Static rules file + **MistakeGuard** (Active Defense against repeating errors). | 🚀 Superior |
| **Self-Learning** | **Skills (`/remember`):** Scans session history to update `CLAUDE.local.md` with patterns. | **Memory Client:** `Memory.add_pattern()` hook to auto-update `ARKA.md` when user strictly corrects the agent. | 🚀 Superior |
| **System Control** | **Limited:** basic file/terminal ops. | **God Mode:** Full OS control via Vision + Mouse/Keyboard (`system_click`, `open_app`). | 🚀 Superior |
| **Tone** | **Objective:** "No fluff, no estimates." | **Professional Objectivity:** System prompt enforcement of "Technical Facts Only". | ✅ Planned |
| **Safety** | **Permissions:** Prompts for tool use. | **Failsafe:** `pyautogui` corner exit + `MistakeGuard` pre-flight checks. | 🚀 Superior |

### Feature Deep Dive: The "Skills" Architecture
User research into `tool-description-skill.md` revealed that Claude Code uses "Skills" for user-defined behaviors (like `/commit` or `/review-pr`).
*   **Antigravity V2 Approach:** We will implement a `SkillRegistry` in `core/skills.py` that allows the user to drop Markdown files into `.arka/skills/` to define new Slash Commands dynamically, matching Claude's extensibility.

---

## 10. Research-Driven Feature Expansion (Web Search Results)

Recent web search results for "Claude Code" and "Google Antigravity" have shaped the final feature set.

### A. From Claude Code (CLI)
*   **Checkpointing/Rewind:** The ability to undo agent actions.
    *   *V2 Implementation:* `tools/git.py` wrapper to auto-commit before major changes, enabling `git reset --hard` for "Undo".
*   **Visual Call Graphs:** Generating dependency trees.
    *   *V2 Implementation:* New tool `generate_graph(path)` using `pydeps` or `graphviz` to render architecture diagrams for the user.

### B. From Google Antigravity (Real Product Reference)
*   **Browser-Based Verification:** The real Antigravity platform emphasizes "tight loops between code and browser verification".
    *   **V2 Implementation:** Our **Phase 3 Browser Tools** are no longer optional. They are critical. We will prioritize `browser_screenshot` to visually verify frontend changes (CSS/React) match the user's intent.

### C. Updated Capabilities Matrix (V4.4)

| Feature | Claude Code | Google Antigravity | **ARKA V2 (Our Build)** |
| :--- | :--- | :--- | :--- |
| **Undo/Rewind** | Native Command | N/A | **Git-based Checkpoints** (Auto-save) |
| **Verification** | Text Output | **Visual Browser Verification** | **Vision-verified Browser Testing** |
| **Context** | Project Files | Full IDE State | **Full OS State** (God Mode) |
| **Extensibility**| Markdown Skills | Multi-Agent Orchestration | **Polyglot Skills** (Markdown + Python) |

---


## 11. Detailed Feature Specs (System Prompt Analysis)

Based on deep analysis of Claude Code's system prompts, we will implement the following high-value features in V2:

### A. The "Plan Mode" Workflow (`core/modes/planning.py`)
*   **Concept:** A distinct mode that strictly forbids code execution until a plan is approved.
*   **Behavior:**
    1.  **Entrance:** Triggered by complex requests (>3 steps).
    2.  **Loop:**
        *   `Explore`: Read files/docs (Read-only).
        *   `Interview`: Ask user clarifying questions (Batch questions).
        *   `Draft`: Update `task.md` or a temporary `current_plan.md`.
    3.  **Exit:** User types "Approved" -> Switches to Execution Mode.
*   **Prompt Engineering:** We will port `agent-prompt-plan-mode-enhanced.md` to our System Prompt.

### B. The `TodoTool` (`tools/todo.py`)
*   **Concept:** A tool for the *Agent* to self-manage its state.
*   **Structure:**
    ```python
    @tool
    def update_todo(tasks: List[Dict[str, str]]):
        """
        Manage session tasks.
        tasks: [{'status': 'pending|in_progress|completed', 'content': 'Fix bug'}]
        Constraint: Only ONE task 'in_progress' at a time.
        """
    ```
*   **UI Integration:** The `rich` interface will render this Todo List in a dedicated panel, separate from the chat stream.

### C. "Professional Objectivity" Tone
*   **System Prompt Injection:** We will adopt Claude's "No Fluff" policy.
    *   *Rule:* "No time estimates. No 'I will try'. No excessive apologies. Just technical facts."
    *   *Logic:* User trusts competency over politeness.

### D. Hooks & Automations (`core/hooks.py`)
*   **Pre-Tool-Use Hook:**
    *   *Action:* `MistakeGuard.check(tool_name, args)`
    *   *Result:* Block execution if it matches a known failure pattern.
*   **Post-Tool-Use Hook:**
    *   *Action:* `Memory.log(tool, result)`
    *   *Auto-Fix:* If `stderr` contains a known error code, inject a "Self-Correction" prompt immediately without waiting for user input.

## 12. "Corner Case" Resolutions (Final Architecture Decisions)

Based on user feedback and research into Claude Code's handling of edge cases, we have finalized the following architectural decisions:

### A. Hardware Dependencies (The Setup Script)
*   **Problem:** "God Mode" tools (`blueutil`, `networksetup`) are not standard on all Macs.
*   **Resolution:** We will implement a `Phase 0` setup script (`scripts/setup.py`) that checks for and installs missing dependencies via Homebrew.
    *   *Command:* `python scripts/setup.py`
    *   *Action:* Checks `brew list`, installs `blueutil`, `ffmpeg` (for vision), etc.

### B. Vision Latency vs. Cost (The "Fast Mode" Switch)
*   **Problem:** GPT-5.2 Vision is accurate but slow (~3s).
*   **Resolution:** We will implement a configurable `VisionClient`.
    *   **Default:** "Accuracy Mode" (GPT-5.2) for complex UI tasks.
    *   **Config:** `config.vision_model = "gpt-4o"` for low-latency, lower-stakes tasks.

### C. Token Safety (Output Truncation)
*   **Problem:** Runaway CLI output (e.g., 5000 lines of build logs) drains credits.
*   **Resolution:** We will mirror Claude Code's "2000 line limit" exactly.
    *   **Default Limit:** 2000 lines for any `run_terminal` output.
    *   **UI:** Show `[Output truncated. 2800 lines hidden. Use --read-more to see full.]`
    *   **Safety:** Smart truncation (Head + Tail) to preserve error messages at the end.

---

