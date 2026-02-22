"""Chat service for real-time messaging between users and support."""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from src.logging_config import log_info, log_error, log_warning, CHAT_MESSAGES_TOTAL


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
    
    def __init__(self):
        # Active WebSocket connections by conversation_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Message history by conversation_id
        self.message_history: Dict[str, List[ChatMessage]] = {}
        # Escalation events
        self.escalations: List[EscalationEvent] = []
        # User connections tracking
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of conversation_ids
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Connect a user to a conversation."""
        await websocket.accept()
        
        async with self._lock:
            # Add to active connections
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = []
            self.active_connections[conversation_id].append(websocket)
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(conversation_id)
            
        log_info("User connected to chat", {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "total_connections": len(self.active_connections[conversation_id])
        })
        
    async def disconnect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Disconnect a user from a conversation."""
        async with self._lock:
            # Remove from active connections
            if conversation_id in self.active_connections:
                if websocket in self.active_connections[conversation_id]:
                    self.active_connections[conversation_id].remove(websocket)
                    if not self.active_connections[conversation_id]:
                        del self.active_connections[conversation_id]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(conversation_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
                    
        log_info("User disconnected from chat", {
            "conversation_id": conversation_id,
            "user_id": user_id
        })
        
    async def send_message(self, message: ChatMessage) -> bool:
        """Send a message to all participants in a conversation."""
        # Store message in history
        async with self._lock:
            if message.conversation_id not in self.message_history:
                self.message_history[message.conversation_id] = []
            self.message_history[message.conversation_id].append(message)
            
        # Broadcast to all connected clients
        if message.conversation_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[message.conversation_id]:
                try:
                    await websocket.send_text(message.json())
                except Exception as e:
                    log_warning("Failed to send message to websocket", {
                        "conversation_id": message.conversation_id,
                        "error": str(e)
                    })
                    disconnected.append(websocket)
            
            # Clean up disconnected clients
            if disconnected:
                async with self._lock:
                    for ws in disconnected:
                        if ws in self.active_connections[message.conversation_id]:
                            self.active_connections[message.conversation_id].remove(ws)
                            
        return True
        
    def get_message_history(self, conversation_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get message history for a conversation."""
        messages = self.message_history.get(conversation_id, [])
        # Return most recent messages
        return messages[-limit:] if len(messages) > limit else messages
        
    def get_user_conversations(self, user_id: str) -> List[str]:
        """Get all conversation IDs for a user."""
        return list(self.user_connections.get(user_id, set()))
        
    async def escalate_conversation(self, conversation_id: str, reason: str, 
                                  metadata: Optional[Dict[str, Any]] = None) -> EscalationEvent:
        """Escalate a conversation to human support."""
        escalation = EscalationEvent(
            id=f"esc_{datetime.utcnow().timestamp()}",
            conversation_id=conversation_id,
            reason=reason,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        async with self._lock:
            self.escalations.append(escalation)
            
        # Notify all connected clients about escalation
        if conversation_id in self.active_connections:
            escalation_notification = {
                "type": "escalation",
                "conversation_id": conversation_id,
                "reason": reason,
                "timestamp": escalation.timestamp.isoformat(),
                "message": "This conversation has been escalated to human support."
            }
            
            disconnected = []
            for websocket in self.active_connections[conversation_id]:
                try:
                    await websocket.send_text(json.dumps(escalation_notification))
                except Exception as e:
                    log_warning("Failed to send escalation notification", {
                        "conversation_id": conversation_id,
                        "error": str(e)
                    })
                    disconnected.append(websocket)
            
            # Clean up disconnected clients
            if disconnected:
                async with self._lock:
                    for ws in disconnected:
                        if ws in self.active_connections[conversation_id]:
                            self.active_connections[conversation_id].remove(ws)
                            
        log_info("Conversation escalated", {
            "conversation_id": conversation_id,
            "reason": reason
        })
        return escalation
        
    def get_escalations(self, conversation_id: Optional[str] = None) -> List[EscalationEvent]:
        """Get escalation events, optionally filtered by conversation."""
        if conversation_id:
            return [e for e in self.escalations if e.conversation_id == conversation_id]
        return self.escalations.copy()


# Global chat manager instance
chat_manager = ChatManager()