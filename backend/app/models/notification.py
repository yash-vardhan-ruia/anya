"""
CareVoice AI Hospital Platform - Notification Model.

Represents outbound notifications sent to patients via SMS, email, or WhatsApp.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class Notification(UUIDMixin, TimestampMixin, Base):
    """Outbound notification sent to a patient.

    Attributes:
        patient_id: FK to the recipient patient.
        type: Notification type (appointment_confirmation, payment_receipt, reminder).
        channel: Delivery channel (sms, email, whatsapp).
        subject: Optional subject line (primarily for email).
        message: Notification message body.
        sent_at: Timestamp when the notification was actually sent.
        is_read: Whether the notification has been read by the patient.
    """

    __tablename__ = "notifications"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Relationships ---
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="notifications",
        lazy="selectin",
    )
