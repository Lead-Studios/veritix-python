# src/manager.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from starlette.websockets import WebSocket

from src.logging_config import log_error, log_info


class TicketScanManager:
    """Manages WebSocket connections for real-time ticket scan broadcasts."""

    def __init__(self, session_timeout_minutes: int = 30) -> None:
        self.active_connections: Set[WebSocket] = set()
        self.connection_activity: Dict[WebSocket, datetime] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task[None]] = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            self.connection_activity[websocket] = datetime.utcnow()
        log_info("WebSocket connected", {"total_connections": len(self.active_connections)})

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)
            self.connection_activity.pop(websocket, None)
        log_info("WebSocket disconnected", {"total_connections": len(self.active_connections)})

    async def broadcast_scan(self, scan_payload: Dict[str, object]) -> None:
        """Broadcast a scan payload to all connected clients."""
        await self._update_activity_for_all()

        async with self._lock:
            connections: List[WebSocket] = list(self.active_connections)

        if not connections:
            log_info("Broadcast called but no active connections")
            return

        log_info("Broadcasting scan", {"connection_count": len(connections)})
        to_remove: List[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(scan_payload)
            except Exception as exc:
                log_error("Error sending to websocket; scheduling removal", {"error": str(exc)})
                to_remove.append(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self.active_connections.discard(ws)
                    self.connection_activity.pop(ws, None)
            log_info("Removed dead connections after broadcast", {"removed_count": len(to_remove)})

    async def _update_activity_for_all(self) -> None:
        """Update activity timestamps for all connections to prevent timeout during broadcast."""
        async with self._lock:
            current_time = datetime.utcnow()
            for ws in self.active_connections:
                self.connection_activity[ws] = current_time

    async def _cleanup_inactive_sessions(self) -> None:
        """Periodically remove connections inactive for longer than the session timeout."""
        while True:
            try:
                await asyncio.sleep(60)
                current_time = datetime.utcnow()
                to_remove: List[WebSocket] = []

                async with self._lock:
                    for ws, last_activity in self.connection_activity.items():
                        if current_time - last_activity > self.session_timeout:
                            to_remove.append(ws)

                if to_remove:
                    async with self._lock:
                        for ws in to_remove:
                            self.active_connections.discard(ws)
                            self.connection_activity.pop(ws, None)
                    log_info("Cleaned up inactive sessions", {"cleanup_count": len(to_remove)})

            except Exception as exc:
                log_error("Error in cleanup task", {"error": str(exc)})
                await asyncio.sleep(60)

    async def start_cleanup_task(self) -> None:
        """Start the background session-cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
            log_info(
                "Started session cleanup task",
                {"timeout_minutes": self.session_timeout.total_seconds() / 60},
            )

    async def stop_cleanup_task(self) -> None:
        """Stop the background session-cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            log_info("Stopped session cleanup task")