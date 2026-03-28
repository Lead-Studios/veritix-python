"""Chat service for real-time messaging between users and support."""
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set, Union

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


class TypingEvent(BaseModel):
    """Ephemeral event indicating a participant is typing."""

    type: Literal["typing"] = "typing"
    sender_id: str
    conversation_id: str
    is_typing: bool


class ReadReceiptEvent(BaseModel):
    """Ephemeral event indicating messages have been read."""

    type: Literal["read_receipt"] = "read_receipt"
    sender_id: str
    conversation_id: str
    last_read_message_id: str


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
        # status: "open" | "escalated" | "assigned" | "resolved"
        self.conversation_statuses: Dict[str, str] = {}
        self.conversation_assignments: Dict[str, Optional[str]] = {}
        self.conversation_escalated_at: Dict[str, datetime] = {}
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

    async def broadcast_event(
        self, event: Union[TypingEvent, ReadReceiptEvent]
    ) -> bool:
        """Broadcast an ephemeral event to all participants without persisting it."""
        conversation_id = event.conversation_id
        if conversation_id not in self.active_connections:
            return True

        disconnected: List[WebSocket] = []
        for websocket in self.active_connections[conversation_id]:
            try:
                await websocket.send_text(event.model_dump_json())
            except Exception as exc:
                log_warning(
                    "Failed to send event to websocket",
                    {"conversation_id": conversation_id, "error": str(exc)},
                )
                disconnected.append(websocket)

        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    if ws in self.active_connections.get(conversation_id, []):
                        self.active_connections[conversation_id].remove(ws)

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
            self.conversation_statuses[conversation_id] = "escalated"
            self.conversation_assignments[conversation_id] = None
            self.conversation_escalated_at[conversation_id] = escalation.timestamp

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

    async def assign_conversation(
        self, conversation_id: str, agent_id: str
    ) -> None:
        """Assign an escalated conversation to a support agent."""
        async with self._lock:
            self.conversation_statuses[conversation_id] = "assigned"
            self.conversation_assignments[conversation_id] = agent_id

        notification = {
            "type": "assignment",
            "conversation_id": conversation_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "This conversation has been assigned to a support agent.",
        }

        if conversation_id in self.active_connections:
            disconnected: List[WebSocket] = []
            for websocket in self.active_connections[conversation_id]:
                try:
                    await websocket.send_text(json.dumps(notification))
                except Exception as exc:
                    log_warning(
                        "Failed to send assignment notification",
                        {"conversation_id": conversation_id, "error": str(exc)},
                    )
                    disconnected.append(websocket)

            if disconnected:
                async with self._lock:
                    for ws in disconnected:
                        if ws in self.active_connections.get(conversation_id, []):
                            self.active_connections[conversation_id].remove(ws)

        log_info(
            "Conversation assigned",
            {"conversation_id": conversation_id, "agent_id": agent_id},
        )

    def get_conversation_status(
        self, conversation_id: str
    ) -> Dict[str, Any]:
        """Return the current status and assignment for a conversation."""
        status = self.conversation_statuses.get(conversation_id, "open")
        assigned_agent_id = self.conversation_assignments.get(conversation_id)
        return {
            "conversation_id": conversation_id,
            "status": status,
            "assigned_agent_id": assigned_agent_id,
        }

    def get_unassigned_queue(self) -> List[Dict[str, Any]]:
        """Return all escalated conversations with no assigned agent, ordered by escalated_at asc."""
        queue = []
        for conv_id, status in self.conversation_statuses.items():
            if status == "escalated" and self.conversation_assignments.get(conv_id) is None:
                escalated_at = self.conversation_escalated_at.get(conv_id)
                # Find the most recent escalation reason for this conversation
                reason = ""
                for esc in reversed(self.escalations):
                    if esc.conversation_id == conv_id:
                        reason = esc.reason
                        break
                queue.append({
                    "conversation_id": conv_id,
                    "escalated_at": escalated_at,
                    "reason": reason,
                })
        queue.sort(key=lambda x: x["escalated_at"] or datetime.min)
        return queue

    def get_escalations(
        self, conversation_id: Optional[str] = None
    ) -> List[EscalationEvent]:
        """Return escalation events, optionally filtered by conversation ID."""
        if conversation_id:
            return [e for e in self.escalations if e.conversation_id == conversation_id]
        return self.escalations.copy()


# Global chat manager instance
chat_manager = ChatManager()