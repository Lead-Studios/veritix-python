"""Centralised SQLAlchemy engine singleton with connection pooling.

All modules that need a database engine should import get_engine() and
get_session() from here rather than creating engines themselves.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings

logger = logging.getLogger("veritix.db")

_engine: Optional[Engine] = None


def get_engine() -> Optional[Engine]:
    """Return the shared SQLAlchemy engine, creating it once on first call.

    Returns None if DATABASE_URL is not configured.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        url = getattr(settings, "DATABASE_URL", None)
        if not url:
            logger.info("DATABASE_URL not set; skipping engine creation")
            return None
        try:
            _engine = create_engine(
                url,
                pool_size=settings.POOL_SIZE,
                max_overflow=settings.POOL_MAX_OVERFLOW,
                pool_timeout=30,
                pool_recycle=1800,
                pool_pre_ping=True,
            )
            logger.info(
                "Database engine created with pool_size=%d, max_overflow=%d",
                settings.POOL_SIZE,
                settings.POOL_MAX_OVERFLOW,
            )
        except Exception as exc:
            logger.error("Failed to create database engine: %s", exc)
            return None
    return _engine


def get_session() -> Optional[Session]:
    """Create and return a new database session, or None if DB is not configured."""
    engine = get_engine()
    if engine is None:
        return None
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_pool_status() -> Dict[str, Any]:
    """Return live connection pool statistics."""
    engine = get_engine()
    if engine is None:
        return {"status": "unavailable", "reason": "DATABASE_URL not configured"}
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }
