import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("getitright.servers.websocket")

class WebSocketVoteServer:
    """Manages real-time bidirectional WebSocket connections for live voting and telemetry."""
    def __init__(self):
        self.active_vote_clients: List[WebSocket] = []
        self.active_telemetry_clients: List[WebSocket] = []

    async def connect_vote(self, websocket: WebSocket):
        await websocket.accept()
        self.active_vote_clients.append(websocket)
        logger.info(f"[WS SERVER] Vote client connected. Total clients: {len(self.active_vote_clients)}")

    def disconnect_vote(self, websocket: WebSocket):
        if websocket in self.active_vote_clients:
            self.active_vote_clients.remove(websocket)
            logger.info(f"[WS SERVER] Vote client disconnected. Total clients: {len(self.active_vote_clients)}")

    async def connect_telemetry(self, websocket: WebSocket):
        await websocket.accept()
        self.active_telemetry_clients.append(websocket)
        logger.info(f"[WS SERVER] Telemetry client connected. Total clients: {len(self.active_telemetry_clients)}")

    def disconnect_telemetry(self, websocket: WebSocket):
        if websocket in self.active_telemetry_clients:
            self.active_telemetry_clients.remove(websocket)
            logger.info(f"[WS SERVER] Telemetry client disconnected. Total clients: {len(self.active_telemetry_clients)}")

    async def broadcast_vote_update(self, poll_id: str, option_id: str, total_votes: int, options_data: List[Dict[str, Any]] = None):
        """Broadcasts real-time vote updates to all connected mobile and web clients."""
        payload = {
            "type": "vote_cast",
            "poll_id": poll_id,
            "option_id": option_id,
            "total_votes": total_votes,
            "options": options_data or []
        }
        msg = json.dumps(payload)
        stale_clients = []
        for client in self.active_vote_clients:
            try:
                await client.send_text(msg)
            except Exception:
                stale_clients.append(client)
        for client in stale_clients:
            self.disconnect_vote(client)

    async def broadcast_telemetry(self, stats: Dict[str, Any]):
        """Broadcasts live database dashboard stats to admin telemetry consumers."""
        msg = json.dumps({"type": "telemetry_update", "data": stats})
        stale_clients = []
        for client in self.active_telemetry_clients:
            try:
                await client.send_text(msg)
            except Exception:
                stale_clients.append(client)
        for client in stale_clients:
            self.disconnect_telemetry(client)

    async def broadcast_notification(self, notif_data: Dict[str, Any]):
        """Broadcasts platform notification to all connected clients (votes + telemetry)."""
        msg = json.dumps({"type": "notification", "data": notif_data})
        all_clients = list(set(self.active_vote_clients + self.active_telemetry_clients))
        stale_clients = []
        for client in all_clients:
            try:
                await client.send_text(msg)
            except Exception:
                stale_clients.append(client)
        for client in stale_clients:
            if client in self.active_vote_clients:
                self.disconnect_vote(client)
            if client in self.active_telemetry_clients:
                self.disconnect_telemetry(client)

ws_server = WebSocketVoteServer()
