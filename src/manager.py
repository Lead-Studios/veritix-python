# app/manager.py
import asyncio
from starlette.websockets import WebSocket
from typing import Set
import logging

logger = logging.getLogger("ticket_scans.manager")

class TicketScanManager:
    def __init__(self):
        # set of active WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info("WebSocket connected. total connections=%d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. total connections=%d", len(self.active_connections))

    async def broadcast_scan(self, scan_payload: dict):
        """
        Broadcasts a scan payload (dict) to all connected clients.
        This awaits send_json on each WebSocket. It removes any dead websockets.
        """
        async with self._lock:
            connections = list(self.active_connections)

        if not connections:
            logger.info("Broadcast called but no active connections.")
            return

        logger.info("Broadcasting scan to %d connection(s).", len(connections))
        to_remove = []
        for ws in connections:
            try:
                await ws.send_json(scan_payload)
            except Exception as e:
                logger.exception("Error sending to websocket; scheduling removal. Error: %s", e)
                to_remove.append(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self.active_connections.discard(ws)
            logger.info("Removed %d dead connection(s) after broadcast.", len(to_remove))
