from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple
import shlex
import structlog
from tools.git import git_commit, git_status
from tools.terminal import run_terminal
from core.session_context import session_context

logger = structlog.get_logger()

@dataclass(frozen=True)
class Skill:
    name: str
    func: Callable[[str], str]
    description: str
    usage: str

class SkillRegistry:
    """
    Manages 'Skills' (Slash Commands).
    Examples: /commit, /help, /status
    """
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.exit_requested: bool = False
        self._planner = None
        self._register_defaults()

    def _register_defaults(self):
        self.register_skill(
            "commit",
            self._skill_commit,
            description="Create a git checkpoint commit",
            usage="/commit <message>",
        )
        self.register_skill(
            "status",
            self._skill_status,
            description="Show git status",
            usage="/status",
        )
        self.register_skill(
            "help",
            self._skill_help,
            description="List available slash commands",
            usage="/help",
        )
        self.register_skill(
            "coding",
            self._skill_coding,
            description="Toggle coding mode",
            usage="/coding [on|off|status]",
        )
        self.register_skill(
            "plan",
            self._skill_plan,
            description="Enter Planning Mode",
            usage="/plan <request>",
        )
        self.register_skill(
            "memory",
            self._skill_memory,
            description="Manage long-term memory",
            usage="/memory <list|show|search|stats|forget|lock|export|import|purge> ...",
        )
        self.register_skill(
            "goals",
            self._skill_goals,
            description="Manage goals",
            usage="/goals <list|advance|complete> ...",
        )
        self.register_skill(
            "mcp",
            self._skill_mcp,
            description="MCP tools and status",
            usage="/mcp <list|status|call|connect|disconnect|tools> ...",
        )
        self.register_skill(
            "exit",
            self._skill_exit,
            description="Exit ARKA",
            usage="/exit",
        )

    def register_skill(self, name: str, func: Callable, description: str = "", usage: str = ""):
        self.skills[name] = Skill(
            name=name,
            func=func,
            description=description or "No description",
            usage=usage or f"/{name}",
        )

    def bind_planner(self, planner) -> None:
        self._planner = planner

    def clear_exit(self) -> None:
        self.exit_requested = False

    def execute_skill(self, command: str) -> str:
        """
        Parses "/command args" and executes the corresponding skill.
        """
        parts = command.strip().split(" ", 1)
        skill_name = parts[0][1:] # remove '/'
        args = parts[1] if len(parts) > 1 else ""

        if not skill_name:
            return self._skill_help("")

        if skill_name in self.skills:
            logger.info("skill_exec", skill=skill_name, args=args)
            return self.skills[skill_name].func(args)
        return f"Unknown skill: {skill_name}. Type /help for list."

    def list_skills(self) -> List[Skill]:
        return [self.skills[name] for name in sorted(self.skills.keys())]

    def get_completion_items(self) -> List[Tuple[str, str]]:
        """Return list of (command, meta) for UI completions."""
        items: List[Tuple[str, str]] = []
        for skill in self.list_skills():
            meta = f"{skill.description} | {skill.usage}"
            items.append((f"/{skill.name}", meta))
        return items

    # --- Default Skills ---
    
    def _skill_commit(self, msg: str) -> str:
        if not msg:
            return "Please provide a commit message. Usage: /commit <message>"
        return git_commit(msg)

    def _skill_status(self, _: str) -> str:
        return git_status()

    def _skill_help(self, _: str) -> str:
        lines = ["Available Skills:"]
        for skill in self.list_skills():
            lines.append(f"- /{skill.name} — {skill.description} (usage: {skill.usage})")
        return "\n".join(lines)

    def _skill_plan(self, args: str) -> str:
        if not self._planner:
            return "Planning unavailable. Restart ARKA."
        request = (args or "").strip()
        if not request:
            return "Usage: /plan <request>"
        return self._planner.start_plan(request)

    def _skill_memory(self, args: str) -> str:
        from tools.memory_tools import (
            memory_search,
            memory_list,
            memory_show,
            memory_import,
            memory_purge,
            memory_forget,
            memory_lock,
            memory_export,
            memory_stats,
        )
        parts = shlex.split(args) if args else []
        if not parts:
            return "Usage: /memory <list|show|search|stats|forget|lock|export|import|purge> ..."
        sub = parts[0].lower()

        if sub in {"list", "ls"}:
            limit = 20
            if len(parts) > 1:
                try:
                    limit = int(parts[1])
                except ValueError:
                    pass
            return memory_list(limit=limit)

        if sub in {"show"}:
            if len(parts) < 2:
                return "Usage: /memory show <fact_id>"
            try:
                fact_id = int(parts[1])
            except ValueError:
                return "fact_id must be an integer."
            return memory_show(fact_id)

        if sub in {"stats"}:
            return memory_stats()

        if sub in {"search", "find"}:
            query_parts = parts[1:]
            if not query_parts:
                return "Usage: /memory search <query> [--limit N]"
            limit = 5
            if "--limit" in query_parts:
                idx = query_parts.index("--limit")
                if idx + 1 < len(query_parts):
                    try:
                        limit = int(query_parts[idx + 1])
                    except ValueError:
                        pass
                del query_parts[idx:idx + 2]
            query_parts_clean = []
            for p in query_parts:
                if p.startswith("limit="):
                    try:
                        limit = int(p.split("=", 1)[1])
                    except ValueError:
                        pass
                    continue
                query_parts_clean.append(p)
            query = " ".join(query_parts_clean).strip()
            if not query:
                return "Usage: /memory search <query> [--limit N]"
            return memory_search(query, limit=limit)

        if sub in {"forget", "delete", "remove"}:
            if len(parts) < 2:
                return "Usage: /memory forget <fact_id>"
            try:
                fact_id = int(parts[1])
            except ValueError:
                return "fact_id must be an integer."
            return memory_forget(fact_id)

        if sub in {"lock"}:
            if len(parts) < 2:
                return "Usage: /memory lock <fact_id>"
            try:
                fact_id = int(parts[1])
            except ValueError:
                return "fact_id must be an integer."
            return memory_lock(fact_id)

        if sub in {"export"}:
            path = parts[1] if len(parts) > 1 else "~/.arka/memory/memory_export.json"
            return memory_export(path)

        if sub in {"import"}:
            if len(parts) < 2:
                return "Usage: /memory import <path>"
            return memory_import(parts[1])

        if sub in {"purge"}:
            older_than_days = None
            if len(parts) > 1:
                try:
                    older_than_days = int(parts[1])
                except ValueError:
                    return "Usage: /memory purge [older_than_days]"
            return memory_purge(older_than_days)

        return "Unknown memory subcommand. Usage: /memory <list|show|search|stats|forget|lock|export|import|purge> ..."

    def _skill_goals(self, args: str) -> str:
        from tools.goal_tools import list_goals, advance_goal, complete_goal
        parts = shlex.split(args) if args else []
        if not parts:
            return "Usage: /goals <list|advance|complete> ..."
        sub = parts[0].lower()
        if sub in {"list", "ls"}:
            return list_goals()
        if sub in {"advance", "next"}:
            if len(parts) < 2:
                return "Usage: /goals advance <goal_id>"
            return advance_goal(parts[1])
        if sub in {"complete", "done"}:
            if len(parts) < 2:
                return "Usage: /goals complete <goal_id>"
            return complete_goal(parts[1])
        return "Unknown goals subcommand. Usage: /goals <list|advance|complete> ..."

    def _skill_mcp(self, args: str) -> str:
        from tools.mcp_tools import list_mcp_tools, call_mcp_tool
        from core.mcp_client import mcp_bridge
        parts = shlex.split(args) if args else []
        if not parts:
            return "Usage: /mcp <list|status|call|connect|disconnect|tools> ..."
        sub = parts[0].lower()
        if sub in {"list", "ls"}:
            return list_mcp_tools()
        if sub in {"status"}:
            status = mcp_bridge.status
            servers = ", ".join(status["connected_servers"]) or "none"
            return f"MCP status: running={status['running']}, servers={servers}, tools={status['total_tools']}"
        if sub in {"tools"}:
            if len(parts) < 2:
                return "Usage: /mcp tools <server_name>"
            server_name = parts[1]
            tools = [t for t in mcp_bridge.list_tools() if t.get("server") == server_name]
            if not tools:
                return f"No tools found for server '{server_name}'."
            lines = [f"📡 MCP Tools ({server_name}):"]
            for t in tools:
                lines.append(f"  • {t['name']}: {t['description']}")
            return "\n".join(lines)
        if sub in {"call"}:
            if len(parts) < 2:
                return "Usage: /mcp call <tool_name> [arguments_json]"
            tool_name = parts[1]
            arguments_json = ""
            if len(parts) > 2:
                arguments_json = " ".join(parts[2:]).strip()
            return call_mcp_tool(tool_name, arguments_json)
        if sub in {"connect"}:
            if len(parts) < 3:
                return "Usage: /mcp connect <name> <command> [args...]"
            name = parts[1]
            command = parts[2]
            args_list = parts[3:] if len(parts) > 3 else []
            try:
                mcp_bridge.connect(name, command, args_list)
                return f"Connected MCP server '{name}'."
            except Exception as e:
                return f"Failed to connect MCP server: {e}"
        if sub in {"disconnect", "close", "stop"}:
            try:
                mcp_bridge.disconnect_all()
                return "Disconnected all MCP servers."
            except Exception as e:
                return f"Failed to disconnect MCP servers: {e}"
        return "Unknown mcp subcommand. Usage: /mcp <list|status|call|connect|disconnect|tools> ..."

    def _skill_exit(self, _: str) -> str:
        self.exit_requested = True
        return "Exiting..."

    def _skill_coding(self, args: str) -> str:
        """
        Toggle coding mode.
        Usage: /coding, /coding on, /coding off, /coding status
        """
        arg = (args or "").strip().lower()
        if arg in {"status", "?", "help"}:
            return f"Mode: {session_context.mode}"
        if arg in {"on", "enable", "1", "true", "coding"}:
            session_context.update_mode("coding")
            return "Coding mode enabled."
        if arg in {"off", "disable", "0", "false", "default", "normal"}:
            session_context.update_mode("default")
            return "Default mode enabled."

        # Toggle if no/unknown args
        new_mode = "coding" if session_context.mode != "coding" else "default"
        session_context.update_mode(new_mode)
        return f"Mode set to {new_mode}."

# Singleton
skill_registry = SkillRegistry()
