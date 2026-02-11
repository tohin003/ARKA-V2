from typing import Any, Dict
import structlog

logger = structlog.get_logger()

class AgentHooks:
    """
    Interceptors for Agent actions.
    Phase 3 will add MistakeGuard and Memory logging here.
    """
    
    @staticmethod
    def pre_tool_execution(tool_name: str, args: Dict[str, Any]) -> bool:
        """
        Run before any tool execution.
        Returns False if execution should be BLOCKED (e.g. by MistakeGuard).
        """
        logger.info("hook_pre_tool", tool=tool_name)
        # TODO Phase 3: Check MistakeGuard
        return True

    @staticmethod
    def post_tool_execution(tool_name: str, result: Any, error: Any = None):
        """
        Run after tool execution to log to Memory/DB.
        """
        status = "error" if error else "success"
        # Log truncation for safety
        res_str = str(result)
        if len(res_str) > 500:
            res_str = res_str[:500] + "...[truncated]"
            
        logger.info("hook_post_tool", tool=tool_name, status=status, result=res_str)
        # TODO Phase 3: Memory.log(tool, result)
