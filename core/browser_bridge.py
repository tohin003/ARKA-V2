"""
core/browser_bridge.py — ARKA Chrome Extension Bridge

WebSocket server that connects ARKA agent to the Chrome extension.
Runs on ws://localhost:7777. Provides synchronous API for agent tools.
"""

import asyncio
import json
import threading
import time
import uuid
import structlog
import os
from typing import Optional, Any

logger = structlog.get_logger()

DEFAULT_HOST = os.getenv("ARKA_BRIDGE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("ARKA_BRIDGE_PORT", "7777"))
COMMAND_TIMEOUT = 30  # seconds


class BrowserBridge:
    """
    WebSocket server that bridges ARKA agent ↔ Chrome extension.
    
    The extension connects as a client. ARKA sends commands
    and receives results synchronously via send_command().
    """

    def __init__(self, port: int = DEFAULT_PORT, host: str = DEFAULT_HOST):
        self.host = host
        self.port = port
        self.connected = False
        self.extension_ws = None
        self._loop = None
        self._thread = None
        self._server = None
        self._pending: dict[str, asyncio.Future] = {}
        self._auth_waiting = False
        self._auth_url = None
        self._started_event = threading.Event()
        self._start_error: Optional[str] = None

    # ─── Lifecycle ────────────────────────────────────────────────────

    def start(self):
        """Start WebSocket server in background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._started_event.clear()
        self._start_error = None
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        
        # Wait for server to start
        for _ in range(20):
            if self._loop:
                break
            time.sleep(0.1)
        # Wait for bind success or error
        self._started_event.wait(timeout=3.0)
        if self._start_error:
            logger.error("browser_bridge_start_failed", error=self._start_error)
        else:
            logger.info("browser_bridge_started", host=self.host, port=self.port)

    def stop(self):
        """Stop the WebSocket server."""
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        self.connected = False
        logger.info("browser_bridge_stopped")

    def _run_server(self):
        """Run the async WebSocket server in a dedicated thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._start_ws_server())
            self._loop.run_forever()
        except Exception as e:
            logger.error("browser_bridge_error", error=str(e))
        finally:
            self._loop.close()

    async def _start_ws_server(self):
        """Start the WebSocket server."""
        try:
            import websockets
            self._server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=20,
            )
            logger.info("ws_server_listening", host=self.host, port=self.port)
            self._started_event.set()
        except Exception as e:
            self._start_error = str(e)
            self._started_event.set()
            logger.error("ws_server_start_failed", error=str(e))
            raise

    async def _handle_connection(self, websocket, path=None):
        """Handle a single extension connection."""
        self.extension_ws = websocket
        self.connected = True
        logger.info("extension_connected")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning("invalid_json", message=message[:100])
        except Exception as e:
            logger.info("extension_disconnected", reason=str(e))
        finally:
            self.connected = False
            self.extension_ws = None

    async def _handle_message(self, data: dict):
        """Process a message from the extension."""
        msg_type = data.get("type")
        msg_id = data.get("id")

        # Handshake
        if msg_type == "handshake":
            logger.info("extension_handshake", agent=data.get("agent"), version=data.get("version"))
            return

        # Auth required signal
        if data.get("status") == "auth_required":
            self._auth_waiting = True
            self._auth_url = data.get("url", "")
            logger.info("auth_required", url=self._auth_url)

        # Response to a pending command
        if msg_id and msg_id in self._pending:
            future = self._pending.pop(msg_id)
            if not future.done():
                future.set_result(data)

    # ─── Command API (sync, called by tools) ──────────────────────────

    def send_command(self, action: str, params: dict = None, timeout: int = COMMAND_TIMEOUT) -> dict:
        """
        Send a command to the Chrome extension and wait for the result.
        
        This is the main API used by agent tools.
        Blocks until the extension responds or timeout.
        """
        # Handle continue_after_auth first (clears auth state)
        if action == "continue_after_auth":
            self._auth_waiting = False
            self._auth_url = None
            return {"status": "ok", "message": "Resumed after authentication."}

        # Auth waiting blocks all other commands
        if self._auth_waiting:
            return {
                "status": "auth_required",
                "error": f"⏸ Waiting for user to log in at: {self._auth_url}. Say 'continue' after logging in."
            }

        if not self.connected or not self.extension_ws:
            return {
                "status": "error",
                "error": "Chrome extension not connected. Ensure Chrome is running and the ARKA extension is installed/enabled. This bridge does not control other browsers (e.g. Comet)."
            }

        msg_id = str(uuid.uuid4())[:8]
        message = json.dumps({
            "id": msg_id,
            "action": action,
            "params": params or {}
        })

        try:
            future = self._loop.create_future()
            self._pending[msg_id] = future

            # Send message from the event loop thread
            asyncio.run_coroutine_threadsafe(
                self.extension_ws.send(message),
                self._loop
            )

            # Wait for response (blocking, with timeout)
            result = self._wait_for_future(future, timeout)
            
            # Check for auth_required in response
            if result and result.get("status") == "auth_required":
                self._auth_waiting = True
                self._auth_url = result.get("url", "")
            
            return result

        except TimeoutError:
            self._pending.pop(msg_id, None)
            return {"status": "error", "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            self._pending.pop(msg_id, None)
            return {"status": "error", "error": str(e)}

    def _wait_for_future(self, future: asyncio.Future, timeout: int) -> dict:
        """Wait for an async future from the sync context."""
        start = time.time()
        while time.time() - start < timeout:
            if future.done():
                return future.result()
            time.sleep(0.05)
        raise TimeoutError()

    # ─── Status ───────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self.connected and self.extension_ws is not None

    @property
    def is_auth_waiting(self) -> bool:
        return self._auth_waiting

    def status(self) -> dict:
        return {
            "connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "auth_waiting": self._auth_waiting,
            "auth_url": self._auth_url,
            "last_error": self._start_error,
        }


# ─── Singleton ────────────────────────────────────────────────────────
browser_bridge = BrowserBridge()
