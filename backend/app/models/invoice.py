"""
CareVoice AI Hospital Platform - Invoice Model.

Represents a financial invoice generated for an appointment,
including subtotal, GST, and total amount in paise.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.patient import Patient
    from app.models.payment import Payment


class Invoice(UUIDMixin, TimestampMixin, Base):
    """Invoice for a hospital appointment.

    All monetary amounts are stored in paise (1 INR = 100 paise)
    to avoid floating point precision issues.

    Attributes:
        appointment_id: FK to the appointment (one invoice per appointment).
        patient_id: FK to the patient.
        invoice_number: Unique human-readable invoice identifier.
        subtotal: Consultation fee before tax, in paise.
        gst_rate: Applicable GST percentage (e.g., 18.0).
        gst_amount: Calculated GST amount in paise.
        total_amount: Subtotal + GST, in paise.
    """

    __tablename__ = "invoices"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Float, nullable=False)
    gst_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Relationships ---
    appointment: Mapped["Appointment"] = relationship(
        "Appointment",
        back_populates="invoice",
        lazy="selectin",
    )
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="invoices",
        lazy="selectin",
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment",
        back_populates="invoice",
        uselist=False,
        lazy="selectin",
    )

    @property
    def patient_name(self) -> str | None:
        return self.patient.full_name if self.patient else None

    @property
    def appointment_date(self) -> datetime | None:
        return self.appointment.appointment_date if self.appointment else None

    @property
    def doctor_name(self) -> str | None:
        return self.appointment.doctor.full_name if (self.appointment and self.appointment.doctor) else None

    @property
    def department_name(self) -> str | None:
        return self.appointment.department.name if (self.appointment and self.appointment.department) else None

    @property
    def status(self) -> str:
        if self.payment:
            return "paid" if self.payment.status == "captured" else "pending"
        return "pending"



