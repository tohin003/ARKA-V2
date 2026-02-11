"""
core/mcp_client.py — MCP Bridge (Phase 5.3)

Bridges the Model Context Protocol (MCP) into ARKA's synchronous tool system.
MCP servers are spawned as subprocesses (stdio transport) and their tools
are made available to the ArkaEngine.

Architecture:
    - MCPBridge: Manages connections to multiple MCP servers.
    - Each server runs as a subprocess (node/python) communicating via stdin/stdout.
    - Tools from MCP servers are listed and can be called by name.
    - Async MCP SDK is bridged to sync via asyncio.run() / event loop threading.
"""

import asyncio
import json
import threading
from typing import Optional, Any
from contextlib import AsyncExitStack
import structlog

logger = structlog.get_logger()

# MCP SDK imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPBridge:
    """
    Manages connections to MCP servers and exposes their tools.
    
    Usage:
        bridge = MCPBridge()
        bridge.connect("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
        tools = bridge.list_tools()
        result = bridge.call_tool("read_file", {"path": "/tmp/test.txt"})
        bridge.disconnect_all()
    """

    def __init__(self):
        self._servers: dict[str, dict] = {}  # name -> {session, params, ...}
        self._tools_cache: list[dict] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._exit_stack: Optional[AsyncExitStack] = None
        self._started = False

    # ─── Event Loop Management ────────────────────────────────────────
    
    def _ensure_loop(self):
        """Ensure we have a running asyncio event loop in a background thread."""
        if self._started:
            return
        
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name="MCP-EventLoop",
            daemon=True,
        )
        self._thread.start()
        self._started = True
        
        # Create exit stack in the loop
        future = asyncio.run_coroutine_threadsafe(
            self._init_exit_stack(), self._loop
        )
        future.result(timeout=5)

    async def _init_exit_stack(self):
        self._exit_stack = AsyncExitStack()

    def _run_async(self, coro):
        """Run an async coroutine from sync code using the background loop."""
        self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)

    # ─── Connection Management ────────────────────────────────────────

    def connect(self, server_name: str, command: str, args: list[str], env: dict = None):
        """
        Connect to an MCP server via stdio transport.
        
        Args:
            server_name: A friendly name for this server (e.g., "filesystem").
            command: The command to run (e.g., "npx", "python", "node").
            args: Arguments for the command (e.g., ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]).
            env: Optional environment variables.
        """
        self._run_async(self._async_connect(server_name, command, args, env))

    async def _async_connect(self, server_name: str, command: str, args: list[str], env: dict = None):
        """Async implementation of connect."""
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
        )

        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio_read, stdio_write = stdio_transport

        session = await self._exit_stack.enter_async_context(
            ClientSession(stdio_read, stdio_write)
        )
        await session.initialize()

        # List tools from this server
        response = await session.list_tools()
        tools = response.tools

        self._servers[server_name] = {
            "session": session,
            "tools": tools,
        }

        # Update cache
        for tool in tools:
            self._tools_cache.append({
                "server": server_name,
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            })

        logger.info(
            "mcp_server_connected",
            server=server_name,
            tools=[t.name for t in tools],
        )

    # ─── Tool Operations ──────────────────────────────────────────────

    def list_tools(self) -> list[dict]:
        """List all tools from all connected MCP servers."""
        return self._tools_cache

    def call_tool(self, tool_name: str, arguments: dict = None) -> str:
        """
        Call a tool on a connected MCP server.
        
        Args:
            tool_name: Name of the tool (e.g., "read_file").
            arguments: Dict of arguments for the tool.
        
        Returns:
            String result from the tool.
        """
        return self._run_async(self._async_call_tool(tool_name, arguments or {}))

    async def _async_call_tool(self, tool_name: str, arguments: dict) -> str:
        """Async implementation of call_tool."""
        # Find which server has this tool
        for server_name, server_info in self._servers.items():
            tool_names = [t.name for t in server_info["tools"]]
            if tool_name in tool_names:
                result = await server_info["session"].call_tool(tool_name, arguments)
                # Extract text content from result
                content_parts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                    else:
                        content_parts.append(str(item))
                return "\n".join(content_parts)

        raise ValueError(f"Tool '{tool_name}' not found on any connected MCP server.")

    # ─── Cleanup ──────────────────────────────────────────────────────

    def disconnect_all(self):
        """Disconnect from all MCP servers and clean up."""
        if not self._started:
            return
        
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._exit_stack.aclose(), self._loop
            )
            future.result(timeout=10)
        except Exception as e:
            logger.warning("mcp_cleanup_error", error=str(e))
        
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)
        
        self._servers.clear()
        self._tools_cache.clear()
        self._started = False
        logger.info("mcp_bridge_shutdown")

    @property
    def status(self):
        return {
            "connected_servers": list(self._servers.keys()),
            "total_tools": len(self._tools_cache),
            "running": self._started,
        }


# Singleton instance
mcp_bridge = MCPBridge()
