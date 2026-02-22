# app/manager.py
import asyncio
from starlette.websockets import WebSocket
from typing import Set, Dict
from datetime import datetime, timedelta
from src.logging_config import log_info, log_error

class TicketScanManager:
    def __init__(self, session_timeout_minutes: int = 30):
        # set of active WebSocket connections
        self.active_connections: Set[WebSocket] = set()
        # track last activity time for each connection
        self.connection_activity: Dict[WebSocket, datetime] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = asyncio.Lock()
        # Start cleanup task
        self._cleanup_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            self.connection_activity[websocket] = datetime.utcnow()
        log_info("WebSocket connected", {
            "total_connections": len(self.active_connections)
        })

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            if websocket in self.connection_activity:
                del self.connection_activity[websocket]
        log_info("WebSocket disconnected", {
            "total_connections": len(self.active_connections)
        })

    async def broadcast_scan(self, scan_payload: dict):
        """
        Broadcasts a scan payload (dict) to all connected clients.
        This awaits send_json on each WebSocket. It removes any dead websockets.
        """
        # Update activity time for all connections before broadcast
        await self._update_activity_for_all()
        
        async with self._lock:
            connections = list(self.active_connections)

        if not connections:
            log_info("Broadcast called but no active connections")
            return

        log_info("Broadcasting scan", {
            "connection_count": len(connections)
        })
        to_remove = []
        for ws in connections:
            try:
                await ws.send_json(scan_payload)
            except Exception as e:
                log_error("Error sending to websocket; scheduling removal", {
                    "error": str(e)
                })
                to_remove.append(ws)

        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self.active_connections.discard(ws)
                    if ws in self.connection_activity:
                        del self.connection_activity[ws]
            log_info("Removed dead connections after broadcast", {
                "removed_count": len(to_remove)
            })

    async def _update_activity_for_all(self):
        """Update activity timestamp for all connections to prevent timeout during broadcast."""
        async with self._lock:
            current_time = datetime.utcnow()
            for ws in self.active_connections:
                self.connection_activity[ws] = current_time

    async def _cleanup_inactive_sessions(self):
        """Remove connections that have been inactive for too long."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                current_time = datetime.utcnow()
                to_remove = []
                
                async with self._lock:
                    for ws, last_activity in self.connection_activity.items():
                        if current_time - last_activity > self.session_timeout:
                            to_remove.append(ws)
                
                if to_remove:
                    async with self._lock:
                        for ws in to_remove:
                            self.active_connections.discard(ws)
                            del self.connection_activity[ws]
                    log_info("Cleaned up inactive sessions", {
                        "cleanup_count": len(to_remove)
                    })
                    
            except Exception as e:
                log_error("Error in cleanup task", {"error": str(e)})
                await asyncio.sleep(60)

    async def start_cleanup_task(self):
        """Start the background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
            log_info("Started session cleanup task", {
                "timeout_minutes": self.session_timeout.total_seconds() / 60
            })

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            log_info("Stopped session cleanup task")
