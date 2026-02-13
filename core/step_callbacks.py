import ast
from typing import List

from smolagents.memory import ActionStep

from core.ui import ui
from core.session_context import session_context


def _collect_tool_calls(code: str, tool_names: set[str]) -> List[str]:
    """Extract tool call names from a code snippet in source order."""
    calls: List[str] = []

    try:
        tree = ast.parse(code)
    except Exception:
        return calls

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr

            if name and name in tool_names:
                calls.append(name)

            self.generic_visit(node)

    Visitor().visit(tree)
    return calls


def summarize_action_step(step: ActionStep, agent):
    """Emit a compact, user-friendly step summary."""
    if not isinstance(step, ActionStep):
        return
    if session_context.interrupt_requested:
        # Raise to abort execution when user requested interrupt (Esc)
        raise KeyboardInterrupt("User interrupt requested.")

    if step.token_usage:
        session_context.update_tokens(
            step.token_usage.input_tokens,
            step.token_usage.output_tokens,
        )

    if not step.code_action:
        return

    tool_names = set(agent.tools.keys()) if hasattr(agent, "tools") else set()
    calls = _collect_tool_calls(step.code_action, tool_names)

    # Drop final_answer from step summaries to reduce noise
    calls = [c for c in calls if c != "final_answer"]

    if calls:
        summary = ", ".join(calls[:6])
        if len(calls) > 6:
            summary += "…"
    else:
        summary = "thinking"

    ui.print_step(step.step_number, summary, session_context.context_usage_str())

    if step.error:
        ui.print_error(str(step.error))
