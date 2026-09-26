"""SQLAlchemy ORM model for conversation persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class ConversationModel(Base):
    """
    Persistent representation of a workflow-building conversation.

    The database stores:
    - conversation metadata
    - conversation messages
    - canonical workflow state
    - generated workflow
    - workflow status

    Business decisions are handled by the application services and
    orchestrator. This model is responsible only for persistence.
    """

    __tablename__ = "conversations"

    # -------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(256),
        default="Untitled workflow",
        nullable=False,
    )

    # -------------------------------------------------------------
    # Conversation data
    # -------------------------------------------------------------

    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )

    # -------------------------------------------------------------
    # Canonical workflow state
    # -------------------------------------------------------------

    state: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # -------------------------------------------------------------
    # Generated workflow
    # -------------------------------------------------------------

    workflow: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # -------------------------------------------------------------
    # Workflow status
    # -------------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(32),
        default="collecting",
        nullable=False,
    )

    # -------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )