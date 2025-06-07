from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    AGENT = "agent"
    ADMIN = "admin"
    CUSTOMER = "customer"

class EscalationStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class EscalationPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MessageType(enum.Enum):
    TEXT = "text"
    FILE = "file"
    SYSTEM = "system"
    ESCALATION = "escalation"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.AGENT)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    escalations_created = relationship("Escalation", foreign_keys="Escalation.created_by", back_populates="creator")
    escalations_assigned = relationship("Escalation", foreign_keys="Escalation.assigned_to", back_populates="assignee")
    chat_sessions = relationship("ChatSession", back_populates="user")
    messages_sent = relationship("ChatMessage", back_populates="sender")

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(EscalationPriority), nullable=False, default=EscalationPriority.MEDIUM)
    status = Column(Enum(EscalationStatus), nullable=False, default=EscalationStatus.OPEN)
    customer_email = Column(String(100), nullable=False)
    customer_name = Column(String(100), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="escalations_created")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="escalations_assigned")
    history = relationship("EscalationHistory", back_populates="escalation")
    chat_session = relationship("ChatSession", back_populates="escalation", uselist=False)

class EscalationHistory(Base):
    __tablename__ = "escalation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    escalation_id = Column(Integer, ForeignKey("escalations.id"), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    field_name = Column(String(50), nullable=False)
    old_value = Column(String(200), nullable=True)
    new_value = Column(String(200), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    escalation = relationship("Escalation", back_populates="history")
    user = relationship("User")

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    escalation_id = Column(Integer, ForeignKey("escalations.id"), nullable=False)
    channel = Column(String(50), nullable=False)
    recipient = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    escalation_id = Column(Integer, ForeignKey("escalations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    escalation = relationship("Escalation", back_populates="chat_session")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User", back_populates="messages_sent")
