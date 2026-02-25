"""Chat service for real-time messaging between users and support."""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket
from pydantic import BaseModel

from src.logging_config import (
    CHAT_MESSAGES_TOTAL,
    log_error,
    log_info,
    log_warning,
)


class ChatMessage(BaseModel):
    """Represents a chat message."""

    id: str
    sender_id: str
    sender_type: str  # "user" or "agent"
    content: str
    timestamp: datetime
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None


class EscalationEvent(BaseModel):
    """Represents an escalation event."""

    id: str
    conversation_id: str
    reason: str  # "timeout", "complex_query", "user_request", etc.
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatManager:
    """Manages chat conversations and WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.message_history: Dict[str, List[ChatMessage]] = {}
        self.escalations: List[EscalationEvent] = []
        self.user_connections: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self, websocket: WebSocket, conversation_id: str, user_id: str
    ) -> None:
        """Connect a user to a conversation."""
        await websocket.accept()

        async with self._lock:
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = []
            self.active_connections[conversation_id].append(websocket)

            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(conversation_id)

        log_info(
            "User connected to chat",
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "total_connections": len(self.active_connections[conversation_id]),
            },
        )

    async def disconnect(
        self, websocket: WebSocket, conversation_id: str, user_id: str
    ) -> None:
        """Disconnect a user from a conversation."""
        async with self._lock:
            if conversation_id in self.active_connections:
                if websocket in self.active_connections[conversation_id]:
                    self.active_connections[conversation_id].remove(websocket)
                    if not self.active_connections[conversation_id]:
                        del self.active_connections[conversation_id]

            if user_id in self.user_connections:
                self.user_connections[user_id].discard(conversation_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

        log_info(
            "User disconnected from chat",
            {"conversation_id": conversation_id, "user_id": user_id},
        )

    async def send_message(self, message: ChatMessage) -> bool:
        """Send a message to all participants in a conversation."""
        async with self._lock:
            if message.conversation_id not in self.message_history:
                self.message_history[message.conversation_id] = []
            self.message_history[message.conversation_id].append(message)

        if message.conversation_id in self.active_connections:
            disconnected: List[WebSocket] = []
            for websocket in self.active_connections[message.conversation_id]:
                try:
                    await websocket.send_text(message.model_dump_json())
                except Exception as exc:
                    log_warning(
                        "Failed to send message to websocket",
                        {"conversation_id": message.conversation_id, "error": str(exc)},
                    )
                    disconnected.append(websocket)

            if disconnected:
                async with self._lock:
                    for ws in disconnected:
                        if ws in self.active_connections.get(message.conversation_id, []):
                            self.active_connections[message.conversation_id].remove(ws)

        return True

    def get_message_history(
        self, conversation_id: str, limit: int = 50
    ) -> List[ChatMessage]:
        """Return the most recent messages for a conversation."""
        messages = self.message_history.get(conversation_id, [])
        return messages[-limit:] if len(messages) > limit else messages

    def get_user_conversations(self, user_id: str) -> List[str]:
        """Return all conversation IDs the user participates in."""
        return list(self.user_connections.get(user_id, set()))

    async def escalate_conversation(
        self,
        conversation_id: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EscalationEvent:
        """Escalate a conversation to human support."""
        escalation = EscalationEvent(
            id=f"esc_{datetime.utcnow().timestamp()}",
            conversation_id=conversation_id,
            reason=reason,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        async with self._lock:
            self.escalations.append(escalation)

        if conversation_id in self.active_connections:
            escalation_notification = {
                "type": "escalation",
                "conversation_id": conversation_id,
                "reason": reason,
                "timestamp": escalation.timestamp.isoformat(),
                "message": "This conversation has been escalated to human support.",
            }

            disconnected: List[WebSocket] = []
            for websocket in self.active_connections[conversation_id]:
                try:
                    await websocket.send_text(json.dumps(escalation_notification))
                except Exception as exc:
                    log_warning(
                        "Failed to send escalation notification",
                        {"conversation_id": conversation_id, "error": str(exc)},
                    )
                    disconnected.append(websocket)

            if disconnected:
                async with self._lock:
                    for ws in disconnected:
                        if ws in self.active_connections.get(conversation_id, []):
                            self.active_connections[conversation_id].remove(ws)

        log_info(
            "Conversation escalated",
            {"conversation_id": conversation_id, "reason": reason},
        )
        return escalation

    def get_escalations(
        self, conversation_id: Optional[str] = None
    ) -> List[EscalationEvent]:
        """Return escalation events, optionally filtered by conversation ID."""
        if conversation_id:
            return [e for e in self.escalations if e.conversation_id == conversation_id]
        return self.escalations.copy()


# Global chat manager instance
chat_manager = ChatManager()