"""
CareVoice AI Hospital Platform - Emergency Incident Model.

Represents a detected emergency during a voice call,
flagged by keyword detection in the AI conversation.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EmergencySeverity
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.call_session import CallSession
    from app.models.patient import Patient


class EmergencyIncident(UUIDMixin, TimestampMixin, Base):
    """Emergency incident detected during an AI voice call.

    Created when the AI detects emergency keywords (e.g., 'chest pain',
    'unconscious') during a conversation. Staff are alerted immediately.

    Attributes:
        call_session_id: FK to the call session that triggered the alert.
        patient_id: FK to the identified patient (nullable if unidentified).
        severity: Emergency severity classification.
        keywords_detected: Comma-separated emergency keywords found.
        caller_phone: Phone number of the caller.
        description: Detailed description from the AI analysis.
        is_resolved: Whether the incident has been resolved by staff.
        resolved_at: Timestamp when the incident was marked resolved.
    """

    __tablename__ = "emergency_incidents"

    call_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("call_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )
    severity: Mapped[EmergencySeverity] = mapped_column(
        String(20),
        default=EmergencySeverity.HIGH,
        nullable=False,
    )
    keywords_detected: Mapped[str] = mapped_column(String(500), nullable=False)
    caller_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- Relationships ---
    call_session: Mapped["CallSession | None"] = relationship(
        "CallSession",
        back_populates="emergency_incidents",
        lazy="selectin",
    )
    patient: Mapped["Patient | None"] = relationship(
        "Patient",
        back_populates="emergency_incidents",
        lazy="selectin",
    )
