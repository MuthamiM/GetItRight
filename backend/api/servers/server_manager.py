import asyncio
import logging
import time
from backend.api.core.config import settings
from backend.api.middleware.telemetry_middleware import telemetry_tracker
from backend.api.servers.websocket_server import ws_server

logger = logging.getLogger("getitright.servers.manager")

class ServerManager:
    """Manages server background services, health monitoring, and telemetry broadcasting."""
    def __init__(self):
        self.is_running = False
        self._background_task = None

    async def start(self):
        self.is_running = True
        logger.info("[SERVER MANAGER] Background services initialized.")
        self._background_task = asyncio.create_task(self._background_loop())

    async def stop(self):
        self.is_running = False
        if self._background_task:
            self._background_task.cancel()
        logger.info("[SERVER MANAGER] Background services stopped.")

    async def _background_loop(self):
        """Periodic background heartbeat to sync database telemetry and broadcast."""
        while self.is_running:
            try:
                await asyncio.sleep(10)
                stats = telemetry_tracker.get_stats()
                if ws_server.active_telemetry_clients:
                    await ws_server.broadcast_telemetry(stats)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SERVER MANAGER ERROR] {e}")

server_manager = ServerManager()
