"""
CareVoice AI Hospital Platform - Patient Model.

Represents a patient registered in the hospital system, typically
created during an AI voice call interaction.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.call_session import CallSession
    from app.models.emergency_incident import EmergencyIncident
    from app.models.invoice import Invoice
    from app.models.notification import Notification
    from app.models.payment import Payment


class Patient(UUIDMixin, TimestampMixin, Base):
    """Patient entity storing demographics and contact information.

    Attributes:
        phone: Unique phone number used for identification during calls.
        full_name: Patient's full legal name.
        email: Optional email address.
        date_of_birth: Optional date of birth.
        gender: Optional gender identifier.
        address: Optional residential address.
        medical_record_number: Auto-generated unique MRN for hospital records.
    """

    __tablename__ = "patients"

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medical_record_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    # --- Relationships ---
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="patient",
        lazy="selectin",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="patient",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="patient",
        lazy="selectin",
    )
    call_sessions: Mapped[list["CallSession"]] = relationship(
        "CallSession",
        back_populates="patient",
        lazy="selectin",
    )
    emergency_incidents: Mapped[list["EmergencyIncident"]] = relationship(
        "EmergencyIncident",
        back_populates="patient",
        lazy="selectin",
    )
