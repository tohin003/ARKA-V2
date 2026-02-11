from typing import List, Dict, Optional
import structlog

logger = structlog.get_logger()

class MistakeGuard:
    """
    Anti-Hallucination & Safety Layer.
    Intercepts agent actions BEFORE they execute to catch common mistakes.
    """
    def __init__(self):
        # Known bad patterns
        self.prohibited_patterns = [
            "rm -rf /", 
            "rm -rf ~",
            ":(){ :|:& };:", # Fork bomb
            "sudo",          # No sudo access by default
        ]
        
        # Lazy coding indicators
        self.lazy_indicators = [
            "# ... rest of code",
            "# ... (implement later)",
            "TODO: finish this",
            "pass # implementation pending"
        ]

    def validate_command(self, command: str) -> Optional[str]:
        """
        Checks a shell command for safety.
        Returns error message if unsafe, else None.
        """
        for pattern in self.prohibited_patterns:
            if pattern in command:
                logger.warning("mistake_guard_block", match=pattern, command=command)
                return f"⛔ SAFETY BLOCK: Command contains prohibited pattern '{pattern}'"
        return None

    def validate_code(self, code: str) -> Optional[str]:
        """
        Checks code for 'lazy' patterns.
        Returns warning message if lazy, else None.
        """
        for indicator in self.lazy_indicators:
            if indicator in code:
                logger.warning("mistake_guard_lazy", match=indicator)
                return f"⚠️ QUALITY CHECK: I found lazy placeholder '{indicator}'. Please write the full code."
        return None

# Singleton
mistake_guard = MistakeGuard()
