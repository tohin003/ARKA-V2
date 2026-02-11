from typing import Callable, Dict
import structlog
from tools.git import git_commit, git_status
from tools.terminal import run_terminal

logger = structlog.get_logger()

class SkillRegistry:
    """
    Manages 'Skills' (Slash Commands).
    Examples: /commit, /help, /status
    """
    def __init__(self):
        self.skills: Dict[str, Callable] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register_skill("commit", self._skill_commit)
        self.register_skill("status", self._skill_status)
        self.register_skill("help", self._skill_help)

    def register_skill(self, name: str, func: Callable):
        self.skills[name] = func

    def execute_skill(self, command: str) -> str:
        """
        Parses "/command args" and executes the corresponding skill.
        """
        parts = command.strip().split(" ", 1)
        skill_name = parts[0][1:] # remove '/'
        args = parts[1] if len(parts) > 1 else ""
        
        if skill_name in self.skills:
            logger.info("skill_exec", skill=skill_name, args=args)
            return self.skills[skill_name](args)
        return f"Unknown skill: {skill_name}. Type /help for list."

    # --- Default Skills ---
    
    def _skill_commit(self, msg: str) -> str:
        if not msg:
            return "Please provide a commit message. Usage: /commit <message>"
        return git_commit(msg)

    def _skill_status(self, _: str) -> str:
        return git_status()

    def _skill_help(self, _: str) -> str:
        return f"Available Skills: {', '.join(['/'+k for k in self.skills.keys()])}"

# Singleton
skill_registry = SkillRegistry()
