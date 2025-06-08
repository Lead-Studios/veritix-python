import uuid
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
import asyncio

from ..models import ChatSession, ChatMessage, User, Escalation, MessageType
from ..schemas import ChatSessionCreate, ChatMessageCreate, ChatSession as ChatSessionSchema
from ..websocket_manager import manager

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, escalation_id: Optional[int] = None) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        db_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            escalation_id=escalation_id,
            is_active=True
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by session ID"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()

    def get_user_sessions(self, user_id: int, active_only: bool = True) -> List[ChatSession]:
        """Get all sessions for a user"""
        query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
        
        if active_only:
            query = query.filter(ChatSession.is_active == True)
        
        return query.order_by(desc(ChatSession.created_at)).all()

    def end_session(self, session_id: str, user_id: int) -> bool:
        """End a chat session"""
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            return False
        
        session.is_active = False
        session.ended_at = datetime.utcnow()
        
        self.db.commit()
        
        # Request feedback after ending session
        asyncio.create_task(self._request_feedback_after_session_end(session_id))
        
        return True

    async def _request_feedback_after_session_end(self, session_id: str):
        """Request feedback after session ends"""
        try:
            from .feedback_service import FeedbackService
            feedback_service = FeedbackService(self.db)
            
            # Wait a moment before requesting feedback
            await asyncio.sleep(2)
            
            # Request feedback
            await feedback_service.request_feedback(session_id)
            
        except Exception as e:
            print(f"Error requesting feedback after session end: {e}")

    def get_session_messages(
        self, 
        session_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages for a chat session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(desc(ChatMessage.created_at)).offset(offset).limit(limit).all()

    def create_message(
        self, 
        session_id: str, 
        sender_id: int, 
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Create a new chat message"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        db_message = ChatMessage(
            session_id=session.id,
            sender_id=sender_id,
            message_type=message_type,
            content=content,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        return db_message

    def update_message(
        self, 
        message_id: int, 
        sender_id: int, 
        new_content: str
    ) -> Optional[ChatMessage]:
        """Update a chat message"""
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.sender_id == sender_id
        ).first()
        
        if not message:
            return None
        
        message.content = new_content
        message.is_edited = True
        message.edited_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        
        return message

    def delete_message(self, message_id: int, sender_id: int) -> bool:
        """Delete a chat message"""
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.sender_id == sender_id
        ).first()
        
        if not message:
            return False
        
        self.db.delete(message)
        self.db.commit()
        return True

    def get_active_sessions_count(self) -> int:
        """Get count of active chat sessions"""
        return self.db.query(ChatSession).filter(ChatSession.is_active == True).count()

    def get_session_participants(self, session_id: str) -> List[User]:
        """Get participants in a chat session (from WebSocket manager)"""
        participant_ids = manager.get_session_participants(session_id)
        
        if not participant_ids:
            return []
        
        return self.db.query(User).filter(User.id.in_(participant_ids)).all()

    def create_system_message(
        self, 
        session_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Create a system message"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Use the session creator as the sender for system messages
        db_message = ChatMessage(
            session_id=session.id,
            sender_id=session.user_id,
            message_type=MessageType.SYSTEM,
            content=content,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        return db_message

    async def broadcast_system_message(
        self, 
        session_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create and broadcast a system message"""
        message = self.create_system_message(session_id, content, metadata)
        
        if message:
            # Broadcast to all session participants
            message_data = {
                "type": "system_message",
                "data": {
                    "id": message.id,
                    "session_id": session_id,
                    "message_type": message.message_type.value,
                    "content": message.content,
                    "metadata": json.loads(message.metadata) if message.metadata else None,
                    "created_at": message.created_at.isoformat()
                }
            }
            
            await manager.broadcast_to_session(session_id, message_data)
        
        return message

    def link_session_to_escalation(self, session_id: str, escalation_id: int) -> bool:
        """Link a chat session to an escalation"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check if escalation exists
        escalation = self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not escalation:
            return False
        
        session.escalation_id = escalation_id
        self.db.commit()
        
        return True

    def get_escalation_session(self, escalation_id: int) -> Optional[ChatSession]:
        """Get chat session for an escalation"""
        return self.db.query(ChatSession).filter(
            ChatSession.escalation_id == escalation_id,
            ChatSession.is_active == True
        ).first()
