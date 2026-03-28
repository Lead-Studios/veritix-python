"""Persistent storage for chat messages and escalations using SQLAlchemy.

NOTE: Active WebSocket connections are intentionally kept in-memory only
(in ChatManager). Only messages and escalation events are persisted here.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert

import src.db as _db

logger = logging.getLogger("veritix.chat_store")

_MESSAGES_TABLE = "chat_messages"
_ESCALATIONS_TABLE = "chat_escalations"


def _get_engine():
    return _db.get_engine()


def _ensure_tables(engine) -> None:
    metadata = MetaData()
    Table(
        _MESSAGES_TABLE,
        metadata,
        Column("id", String, primary_key=True),
        Column("conversation_id", String, nullable=False),
        Column("sender_id", String, nullable=False),
        Column("sender_type", String, nullable=False),
        Column("content", Text, nullable=False),
        Column("timestamp", DateTime, nullable=False),
        Column("metadata_json", Text),
    )
    Table(
        _ESCALATIONS_TABLE,
        metadata,
        Column("id", String, primary_key=True),
        Column("conversation_id", String, nullable=False),
        Column("reason", String, nullable=False),
        Column("timestamp", DateTime, nullable=False),
        Column("metadata_json", Text),
    )
    with engine.begin() as conn:
        metadata.create_all(conn)  # type: ignore[arg-type]


class ChatStore:
    """Persists chat messages and escalation events to Postgres."""

    def __init__(self) -> None:
        self._ready = False

    def _init(self, engine) -> None:
        if not self._ready:
            try:
                _ensure_tables(engine)
                self._ready = True
            except Exception as exc:
                logger.error("ChatStore: failed to create tables: %s", exc)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def save_message(self, message: Any) -> None:
        """Persist a ChatMessage to the DB (best-effort)."""
        engine = _get_engine()
        if engine is None:
            return
        self._init(engine)
        import json
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"INSERT INTO {_MESSAGES_TABLE} "  # noqa: S608
                        "(id, conversation_id, sender_id, sender_type, content, timestamp, metadata_json) "
                        "VALUES (:id, :conv, :sender, :stype, :content, :ts, :meta) "
                        "ON CONFLICT (id) DO NOTHING"
                    ),
                    {
                        "id": message.id,
                        "conv": message.conversation_id,
                        "sender": message.sender_id,
                        "stype": message.sender_type,
                        "content": message.content,
                        "ts": message.timestamp,
                        "meta": json.dumps(message.metadata or {}),
                    },
                )
        except Exception as exc:
            logger.error("ChatStore: save_message failed: %s", exc)

    def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve the most recent messages for a conversation from DB."""
        engine = _get_engine()
        if engine is None:
            return []
        self._init(engine)
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    text(
                        f"SELECT id, conversation_id, sender_id, sender_type, content, timestamp, metadata_json "  # noqa: S608
                        f"FROM {_MESSAGES_TABLE} "
                        "WHERE conversation_id = :conv "
                        "ORDER BY timestamp DESC "
                        "LIMIT :lim"
                    ),
                    {"conv": conversation_id, "lim": limit},
                ).fetchall()
            return [
                {
                    "id": r[0],
                    "conversation_id": r[1],
                    "sender_id": r[2],
                    "sender_type": r[3],
                    "content": r[4],
                    "timestamp": r[5],
                    "metadata": r[6],
                }
                for r in reversed(rows)
            ]
        except Exception as exc:
            logger.error("ChatStore: get_messages failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Escalations
    # ------------------------------------------------------------------

    def save_escalation(self, escalation: Any) -> None:
        """Persist an EscalationEvent to the DB (best-effort)."""
        engine = _get_engine()
        if engine is None:
            return
        self._init(engine)
        import json
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"INSERT INTO {_ESCALATIONS_TABLE} "  # noqa: S608
                        "(id, conversation_id, reason, timestamp, metadata_json) "
                        "VALUES (:id, :conv, :reason, :ts, :meta) "
                        "ON CONFLICT (id) DO NOTHING"
                    ),
                    {
                        "id": escalation.id,
                        "conv": escalation.conversation_id,
                        "reason": escalation.reason,
                        "ts": escalation.timestamp,
                        "meta": json.dumps(escalation.metadata or {}),
                    },
                )
        except Exception as exc:
            logger.error("ChatStore: save_escalation failed: %s", exc)


# Singleton
chat_store = ChatStore()
