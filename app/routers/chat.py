from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.chat_service import ChatService
from ..models import User, ChatSession as ChatSessionModel, ChatMessage as ChatMessageModel
from ..schemas import (
    ChatSession, ChatSessionCreate, ChatMessage, ChatMessageCreate,
    SuccessResponse, UserPresence
)
from ..websocket_manager import ChatWebSocketHandler, manager

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# REST API Endpoints

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    chat_service = ChatService(db)
    
    session = chat_service.create_session(
        user_id=current_user.id,
        escalation_id=session_data.escalation_id
    )
    
    return session

@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(
    active_only: bool = Query(True, description="Return only active sessions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user"""
    chat_service = ChatService(db)
    sessions = chat_service.get_user_sessions(current_user.id, active_only)
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    chat_service = ChatService(db)
    session = chat_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Check if user has access to this session
    if session.user_id != current_user.id and current_user.role.value not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session

@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def end_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a chat session"""
    chat_service = ChatService(db)
    
    success = chat_service.end_session(session_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Chat session not found or already ended")
    
    # Notify participants that session ended
    await chat_service.broadcast_system_message(
        session_id,
        f"Chat session ended by {current_user.full_name}",
        {"action": "session_ended", "ended_by": current_user.id}
    )
    
    return SuccessResponse(message="Chat session ended successfully")

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a chat session"""
    chat_service = ChatService(db)
    
    # Check if session exists and user has access
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if session.user_id != current_user.id and current_user.role.value not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = chat_service.get_session_messages(session_id, limit, offset)
    return messages

@router.post("/sessions/{session_id}/messages", response_model=ChatMessage)
async def send_message_rest(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message via REST API (fallback for non-WebSocket clients)"""
    chat_service = ChatService(db)
    
    # Check if session exists and user has access
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if session.user_id != current_user.id and current_user.role.value not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create message
    message = chat_service.create_message(
        session_id=session_id,
        sender_id=current_user.id,
        content=message_data.content,
        message_type=message_data.message_type,
        metadata=message_data.metadata
    )
    
    if not message:
        raise HTTPException(status_code=400, detail="Failed to create message")
    
    # Broadcast message to WebSocket connections
    message_data = {
        "type": "new_message",
        "data": {
            "id": message.id,
            "session_id": session_id,
            "sender_id": current_user.id,
            "sender_username": current_user.username,
            "sender_full_name": current_user.full_name,
            "message_type": message.message_type.value,
            "content": message.content,
            "metadata": json.loads(message.metadata) if message.metadata else None,
            "created_at": message.created_at.isoformat(),
            "is_edited": message.is_edited
        }
    }
    
    await manager.broadcast_to_session(session_id, message_data)
    
    return message

@router.put("/messages/{message_id}", response_model=ChatMessage)
async def update_message(
    message_id: int,
    new_content: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a chat message"""
    chat_service = ChatService(db)
    
    message = chat_service.update_message(message_id, current_user.id, new_content)
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or access denied")
    
    # Broadcast message update to WebSocket connections
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == message.session_id).first()
    if session:
        update_data = {
            "type": "message_updated",
            "data": {
                "id": message.id,
                "session_id": session.session_id,
                "content": message.content,
                "is_edited": message.is_edited,
                "edited_at": message.edited_at.isoformat() if message.edited_at else None
            }
        }
        
        await manager.broadcast_to_session(session.session_id, update_data)
    
    return message

@router.delete("/messages/{message_id}", response_model=SuccessResponse)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat message"""
    chat_service = ChatService(db)
    
    # Get message details before deletion
    message = db.query(ChatMessageModel).filter(
        ChatMessageModel.id == message_id,
        ChatMessageModel.sender_id == current_user.id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or access denied")
    
    session = db.query(ChatSessionModel).filter(ChatSessionModel.id == message.session_id).first()
    
    success = chat_service.delete_message(message_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete message")
    
    # Broadcast message deletion to WebSocket connections
    if session:
        delete_data = {
            "type": "message_deleted",
            "data": {
                "id": message_id,
                "session_id": session.session_id
            }
        }
        
        await manager.broadcast_to_session(session.session_id, delete_data)
    
    return SuccessResponse(message="Message deleted successfully")

@router.get("/sessions/{session_id}/participants", response_model=List[UserPresence])
async def get_session_participants(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get participants in a chat session"""
    chat_service = ChatService(db)
    
    # Check if session exists and user has access
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    if session.user_id != current_user.id and current_user.role.value not in ["admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    participants = chat_service.get_session_participants(session_id)
    
    return [
        UserPresence(
            user_id=user.id,
            username=user.username,
            is_online=manager.is_user_online(user.id),
            last_seen=user.last_seen,
            current_session=session_id if manager.is_user_online(user.id) else None
        )
        for user in participants
    ]

@router.get("/online-users", response_model=List[UserPresence])
async def get_online_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of online users"""
    online_user_ids = manager.get_online_users()
    
    if not online_user_ids:
        return []
    
    users = db.query(User).filter(User.id.in_(online_user_ids)).all()
    
    return [
        UserPresence(
            user_id=user.id,
            username=user.username,
            is_online=True,
            last_seen=user.last_seen,
            current_session=None  # Could be enhanced to show current session
        )
        for user in users
    ]

# WebSocket Endpoint

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(..., description="JWT token for authentication"),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    try:
        # Authenticate user
        from ..services.auth_service import verify_token
        token_data = verify_token(token)
        
        if not token_data or not token_data.user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get user
        user = db.query(User).filter(User.id == token_data.user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=4002, reason="User not found or inactive")
            return
        
        # Update user online status
        user.is_online = True
        db.commit()
        
        # Handle WebSocket connection
        handler = ChatWebSocketHandler(websocket, user.id, session_id, db)
        await handler.handle_connection()
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass
    finally:
        # Update user offline status
        try:
            user = db.query(User).filter(User.id == token_data.user_id).first()
            if user:
                user.is_online = False
                user.last_seen = datetime.utcnow()
                db.commit()
        except:
            pass

# Link chat session to escalation
@router.post("/sessions/{session_id}/link-escalation/{escalation_id}", response_model=SuccessResponse)
async def link_session_to_escalation(
    session_id: str,
    escalation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link a chat session to an escalation"""
    chat_service = ChatService(db)
    
    success = chat_service.link_session_to_escalation(session_id, escalation_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to link session to escalation")
    
    # Notify participants
    await chat_service.broadcast_system_message(
        session_id,
        f"Chat session linked to escalation #{escalation_id}",
        {"action": "escalation_linked", "escalation_id": escalation_id}
    )
    
    return SuccessResponse(message="Session linked to escalation successfully")
