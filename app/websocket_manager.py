import json
import uuid
from typing import Dict, List, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import logging

from .models import User, ChatSession, ChatMessage, MessageType
from .database import get_db
from .schemas import ChatWebSocketMessage, WebSocketMessage, UserPresence

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Active WebSocket connections: {user_id: {session_id: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # Session participants: {session_id: {user_id}}
        self.session_participants: Dict[str, Set[int]] = {}
        # User sessions: {user_id: {session_id}}
        self.user_sessions: Dict[int, Set[str]] = {}
        # Typing indicators: {session_id: {user_id: timestamp}}
        self.typing_indicators: Dict[str, Dict[int, datetime]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, session_id: str):
        """Connect a user to a WebSocket session"""
        await websocket.accept()
        
        # Initialize user connections if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.user_sessions[user_id] = set()
        
        # Store the connection
        self.active_connections[user_id][session_id] = websocket
        self.user_sessions[user_id].add(session_id)
        
        # Add user to session participants
        if session_id not in self.session_participants:
            self.session_participants[session_id] = set()
        self.session_participants[session_id].add(user_id)
        
        logger.info(f"User {user_id} connected to session {session_id}")
        
        # Notify other participants about user joining
        await self.broadcast_to_session(
            session_id,
            {
                "type": "user_joined",
                "data": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            exclude_user=user_id
        )

    async def disconnect(self, user_id: int, session_id: str):
        """Disconnect a user from a WebSocket session"""
        try:
            # Remove the connection
            if user_id in self.active_connections:
                if session_id in self.active_connections[user_id]:
                    del self.active_connections[user_id][session_id]
                
                # Remove session from user sessions
                if user_id in self.user_sessions:
                    self.user_sessions[user_id].discard(session_id)
                
                # Clean up empty user connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_sessions:
                        del self.user_sessions[user_id]
            
            # Remove user from session participants
            if session_id in self.session_participants:
                self.session_participants[session_id].discard(user_id)
                
                # Clean up empty sessions
                if not self.session_participants[session_id]:
                    del self.session_participants[session_id]
                    if session_id in self.typing_indicators:
                        del self.typing_indicators[session_id]
            
            # Remove typing indicator
            if session_id in self.typing_indicators:
                self.typing_indicators[session_id].pop(user_id, None)
            
            logger.info(f"User {user_id} disconnected from session {session_id}")
            
            # Notify other participants about user leaving
            await self.broadcast_to_session(
                session_id,
                {
                    "type": "user_left",
                    "data": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                exclude_user=user_id
            )
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id} from session {session_id}: {e}")

    async def send_personal_message(self, message: dict, user_id: int, session_id: str):
        """Send a message to a specific user in a specific session"""
        try:
            if (user_id in self.active_connections and 
                session_id in self.active_connections[user_id]):
                websocket = self.active_connections[user_id][session_id]
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message to user {user_id}: {e}")
            await self.disconnect(user_id, session_id)

    async def broadcast_to_session(self, session_id: str, message: dict, exclude_user: Optional[int] = None):
        """Broadcast a message to all participants in a session"""
        if session_id not in self.session_participants:
            return
        
        participants = self.session_participants[session_id].copy()
        if exclude_user:
            participants.discard(exclude_user)
        
        # Send message to all participants
        for user_id in participants:
            await self.send_personal_message(message, user_id, session_id)

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Broadcast a message to all sessions of a specific user"""
        if user_id not in self.user_sessions:
            return
        
        sessions = self.user_sessions[user_id].copy()
        for session_id in sessions:
            await self.send_personal_message(message, user_id, session_id)

    async def handle_typing_indicator(self, user_id: int, session_id: str, is_typing: bool):
        """Handle typing indicators"""
        if session_id not in self.typing_indicators:
            self.typing_indicators[session_id] = {}
        
        if is_typing:
            self.typing_indicators[session_id][user_id] = datetime.utcnow()
        else:
            self.typing_indicators[session_id].pop(user_id, None)
        
        # Broadcast typing status to other participants
        await self.broadcast_to_session(
            session_id,
            {
                "type": "typing_indicator",
                "data": {
                    "user_id": user_id,
                    "is_typing": is_typing,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            exclude_user=user_id
        )

    def get_session_participants(self, session_id: str) -> List[int]:
        """Get list of participants in a session"""
        return list(self.session_participants.get(session_id, set()))

    def get_user_sessions(self, user_id: int) -> List[str]:
        """Get list of sessions for a user"""
        return list(self.user_sessions.get(user_id, set()))

    def is_user_online(self, user_id: int) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections and bool(self.active_connections[user_id])

    def get_online_users(self) -> List[int]:
        """Get list of all online users"""
        return list(self.active_connections.keys())

    async def cleanup_stale_connections(self):
        """Clean up stale typing indicators and connections"""
        current_time = datetime.utcnow()
        
        # Clean up typing indicators older than 10 seconds
        for session_id in list(self.typing_indicators.keys()):
            for user_id in list(self.typing_indicators[session_id].keys()):
                last_typing = self.typing_indicators[session_id][user_id]
                if (current_time - last_typing).seconds > 10:
                    await self.handle_typing_indicator(user_id, session_id, False)

# Global connection manager instance
manager = ConnectionManager()

class ChatWebSocketHandler:
    def __init__(self, websocket: WebSocket, user_id: int, session_id: str, db: Session):
        self.websocket = websocket
        self.user_id = user_id
        self.session_id = session_id
        self.db = db

    async def handle_connection(self):
        """Handle WebSocket connection lifecycle"""
        try:
            await manager.connect(self.websocket, self.user_id, self.session_id)
            
            # Send connection confirmation
            await self.send_message({
                "type": "connection_established",
                "data": {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "participants": manager.get_session_participants(self.session_id)
                }
            })
            
            # Listen for messages
            while True:
                try:
                    data = await self.websocket.receive_text()
                    message = json.loads(data)
                    await self.handle_message(message)
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await self.send_error("Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    await self.send_error("Internal server error")
                    
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            await manager.disconnect(self.user_id, self.session_id)

    async def handle_message(self, message: dict):
        """Handle incoming WebSocket messages"""
        try:
            ws_message = ChatWebSocketMessage(**message)
            
            if ws_message.action == "send_message":
                await self.handle_send_message(ws_message)
            elif ws_message.action == "typing":
                await self.handle_typing(True)
            elif ws_message.action == "stop_typing":
                await self.handle_typing(False)
            elif ws_message.action == "get_participants":
                await self.handle_get_participants()
            else:
                await self.send_error(f"Unknown action: {ws_message.action}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error("Invalid message format")

    async def handle_send_message(self, ws_message: ChatWebSocketMessage):
        """Handle sending a chat message"""
        try:
            # Get chat session
            chat_session = self.db.query(ChatSession).filter(
                ChatSession.session_id == self.session_id,
                ChatSession.is_active == True
            ).first()
            
            if not chat_session:
                await self.send_error("Chat session not found")
                return
            
            # Create message in database
            db_message = ChatMessage(
                session_id=chat_session.id,
                sender_id=self.user_id,
                message_type=ws_message.message_type or MessageType.TEXT,
                content=ws_message.message,
                metadata=json.dumps(ws_message.metadata) if ws_message.metadata else None
            )
            
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            
            # Get sender info
            sender = self.db.query(User).filter(User.id == self.user_id).first()
            
            # Broadcast message to all session participants
            message_data = {
                "type": "new_message",
                "data": {
                    "id": db_message.id,
                    "session_id": self.session_id,
                    "sender_id": self.user_id,
                    "sender_username": sender.username,
                    "sender_full_name": sender.full_name,
                    "message_type": db_message.message_type.value,
                    "content": db_message.content,
                    "metadata": json.loads(db_message.metadata) if db_message.metadata else None,
                    "created_at": db_message.created_at.isoformat(),
                    "is_edited": db_message.is_edited
                }
            }
            
            await manager.broadcast_to_session(self.session_id, message_data)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await self.send_error("Failed to send message")

    async def handle_typing(self, is_typing: bool):
        """Handle typing indicators"""
        await manager.handle_typing_indicator(self.user_id, self.session_id, is_typing)

    async def handle_get_participants(self):
        """Handle request for session participants"""
        participants = manager.get_session_participants(self.session_id)
        
        # Get participant details from database
        users = self.db.query(User).filter(User.id.in_(participants)).all()
        participant_data = [
            {
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "is_online": manager.is_user_online(user.id)
            }
            for user in users
        ]
        
        await self.send_message({
            "type": "participants_list",
            "data": {
                "session_id": self.session_id,
                "participants": participant_data
            }
        })

    async def send_message(self, message: dict):
        """Send message to this WebSocket connection"""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def send_error(self, error_message: str):
        """Send error message to this WebSocket connection"""
        await self.send_message({
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
