"""
tools/mcp_tools.py — MCP Tools for ARKA (Phase 5.3)

Exposes MCP server tools to the ArkaEngine via smolagents @tool decorator.
The agent can:
    1. List available MCP tools across all connected servers.
    2. Call any MCP tool by name with JSON arguments.
"""

from smolagents import tool
from core.mcp_client import mcp_bridge
import json


@tool
def list_mcp_tools() -> str:
    """
    Lists all tools available from connected MCP servers.
    Use this to discover what external tools are available before calling them.
    
    Returns a formatted list of tool names and descriptions.
    """
    tools = mcp_bridge.list_tools()
    if not tools:
        return "No MCP servers connected. No external tools available."
    
    lines = [f"📡 MCP Tools Available ({len(tools)} total):"]
    for t in tools:
        lines.append(f"  • {t['name']} ({t['server']}): {t['description']}")
    return "\n".join(lines)


@tool
def call_mcp_tool(tool_name: str, arguments_json: str) -> str:
    """
    Calls a tool on a connected MCP server.
    
    Use `list_mcp_tools()` first to see available tools and their schemas.
    
    Args:
        tool_name: The name of the MCP tool to call (e.g., "read_file").
        arguments_json: A JSON string of arguments for the tool (e.g., '{"path": "/tmp/test.txt"}').
    """
    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in arguments_json: {e}"
    
    try:
        result = mcp_bridge.call_tool(tool_name, args)
        return result
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"MCP tool call failed: {str(e)}"
