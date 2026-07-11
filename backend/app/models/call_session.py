"""
CareVoice AI Hospital Platform - Call Session Model.

Represents a browser WebSocket voice session with the Gemini AI conversational agent,
tracking the session lifecycle and conversation state machine.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CallStatus, ConversationState
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class CallSession(UUIDMixin, TimestampMixin, Base):

    """Voice session between a patient and the Gemini AI assistant via browser WebSocket.

    Tracks the session lifecycle, conversation state machine state,
    and full transcript of the interaction.

    Attributes:
        patient_id: FK to the identified patient (nullable until identified).
        session_sid: Unique session identifier (prefixed with 'web_' for browser sessions).
        from_number: Caller identifier (phone number or 'web' for browser sessions).
        status: Current session lifecycle status.
        started_at: Timestamp when the session connected.
        ended_at: Timestamp when the session ended.
        conversation_state: Current state in the conversation flow.
        transcript: Full conversation transcript text.
    """

    __tablename__ = "call_sessions"

    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_sid: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    from_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[CallStatus] = mapped_column(
        String(20),
        default=CallStatus.INITIATED,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    conversation_state: Mapped[ConversationState] = mapped_column(
        String(20),
        default=ConversationState.GREETING,
        nullable=False,
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    patient: Mapped["Patient | None"] = relationship(
        "Patient",
        back_populates="call_sessions",
        lazy="selectin",
    )

