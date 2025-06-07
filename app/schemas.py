from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    AGENT = "agent"
    ADMIN = "admin"
    CUSTOMER = "customer"

class EscalationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class EscalationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MessageType(str, Enum):
    TEXT = "text"
    FILE = "file"
    SYSTEM = "system"
    ESCALATION = "escalation"

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.AGENT

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_online: bool
    last_seen: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Escalation Schemas
class EscalationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: EscalationPriority = EscalationPriority.MEDIUM
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=100)

class EscalationCreate(EscalationBase):
    pass

class EscalationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    priority: Optional[EscalationPriority] = None
    status: Optional[EscalationStatus] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None

class Escalation(EscalationBase):
    id: int
    status: EscalationStatus
    created_by: int
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    creator: User
    assignee: Optional[User] = None

    class Config:
        from_attributes = True

# Chat Schemas
class ChatSessionBase(BaseModel):
    escalation_id: Optional[int] = None

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: int
    session_id: str
    user_id: int
    is_active: bool
    created_at: datetime
    ended_at: Optional[datetime] = None
    user: User
    escalation: Optional[Escalation] = None

    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    message_type: MessageType = MessageType.TEXT
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    sender_id: int
    is_edited: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    sender: User

    class Config:
        from_attributes = True

# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatWebSocketMessage(BaseModel):
    action: str  # "send_message", "join_session", "leave_session", "typing", "stop_typing"
    session_id: Optional[str] = None
    message: Optional[str] = None
    message_type: Optional[MessageType] = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None

class UserPresence(BaseModel):
    user_id: int
    username: str
    is_online: bool
    last_seen: datetime
    current_session: Optional[str] = None

# Notification Schemas
class NotificationCreate(BaseModel):
    channels: List[str] = Field(..., min_items=1)
    message: str = Field(..., min_length=1)
    priority: Optional[str] = "normal"

class NotificationResponse(BaseModel):
    success: bool
    message: str
    failed_channels: List[str] = []

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Dashboard Schemas
class DashboardStats(BaseModel):
    total_escalations: int
    open_escalations: int
    in_progress_escalations: int
    resolved_today: int
    active_chat_sessions: int
    online_agents: int
    average_resolution_time: Optional[float] = None

class EscalationsByPriority(BaseModel):
    low: int
    medium: int
    high: int
    critical: int

class EscalationsByStatus(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int

# Response Schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
