"""Analytics models for tracking ticket scans, transfers, and invalid attempts."""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.config import get_settings


Base = declarative_base()


class TicketScan(Base):
    """Model for tracking ticket scans."""
    __tablename__ = 'ticket_scans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(100), nullable=False, index=True)
    event_id = Column(String(100), nullable=False, index=True)
    scanner_id = Column(String(100), nullable=True)
    scan_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    is_valid = Column(Boolean, nullable=False, default=True)
    location = Column(String(200), nullable=True)
    device_info = Column(Text, nullable=True)
    additional_metadata = Column(Text, nullable=True)  # JSON string for flexible metadata
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ticket_scans_event_timestamp', 'event_id', 'scan_timestamp'),
        Index('idx_ticket_scans_valid', 'is_valid'),
    )


class TicketTransfer(Base):
    """Model for tracking ticket transfers."""
    __tablename__ = 'ticket_transfers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(100), nullable=False, index=True)
    event_id = Column(String(100), nullable=False, index=True)
    from_user_id = Column(String(100), nullable=False)
    to_user_id = Column(String(100), nullable=False)
    transfer_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    transfer_reason = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    is_successful = Column(Boolean, nullable=False, default=True)
    additional_metadata = Column(Text, nullable=True)  # JSON string for flexible metadata
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ticket_transfers_event_timestamp', 'event_id', 'transfer_timestamp'),
        Index('idx_ticket_transfers_successful', 'is_successful'),
    )


class InvalidAttempt(Base):
    """Model for tracking invalid attempts (failed scans, transfers, etc.)."""
    __tablename__ = 'invalid_attempts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_type = Column(String(50), nullable=False, index=True)  # 'scan', 'transfer', 'validation', etc.
    ticket_id = Column(String(100), nullable=True, index=True)
    event_id = Column(String(100), nullable=True, index=True)
    attempt_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    reason = Column(String(200), nullable=False)  # 'invalid_qr', 'expired_ticket', 'unauthorized_transfer', etc.
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    additional_metadata = Column(Text, nullable=True)  # JSON string for flexible metadata
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_invalid_attempts_type_timestamp', 'attempt_type', 'attempt_timestamp'),
        Index('idx_invalid_attempts_event', 'event_id'),
    )


class AnalyticsStats(Base):
    """Model for storing pre-calculated analytics statistics."""
    __tablename__ = 'analytics_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), nullable=False, index=True)
    stat_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    scan_count = Column(Integer, default=0)
    transfer_count = Column(Integer, default=0)
    invalid_attempt_count = Column(Integer, default=0)
    valid_scan_count = Column(Integer, default=0)
    invalid_scan_count = Column(Integer, default=0)
    successful_transfer_count = Column(Integer, default=0)
    failed_transfer_count = Column(Integer, default=0)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_analytics_stats_event_date', 'event_id', 'stat_date'),
    )


def get_database_url():
    """Get database URL from centralized settings."""
    return get_settings().DATABASE_URL


def get_engine():
    """Create database engine."""
    return create_engine(get_database_url())


def get_session():
    """Create database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    """Initialize the database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
