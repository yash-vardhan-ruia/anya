"""
CareVoice AI Hospital Platform - Appointment Model.

Represents a booked appointment linking a patient, doctor, slot, and department.
"""

import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AppointmentStatus
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.doctor import Doctor
    from app.models.invoice import Invoice
    from app.models.patient import Patient
    from app.models.slot import DoctorSlot


class Appointment(UUIDMixin, TimestampMixin, Base):
    """Appointment linking a patient to a doctor at a specific time slot.

    Attributes:
        patient_id: FK to the patient.
        doctor_id: FK to the doctor.
        slot_id: FK to the booked slot (unique — one appointment per slot).
        department_id: FK to the department.
        appointment_date: Calendar date of the appointment.
        start_time: Start time of the appointment.
        end_time: End time of the appointment.
        status: Current appointment lifecycle status.
        symptoms: Patient-reported symptoms captured during the call.
        notes: Additional notes from the AI or doctor.
    """

    __tablename__ = "appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctor_slots.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        String(20),
        default=AppointmentStatus.PENDING,
        nullable=False,
    )
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Relationships ---
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="appointments",
        lazy="selectin",
    )
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="appointments",
        lazy="selectin",
    )
    slot: Mapped["DoctorSlot"] = relationship(
        "DoctorSlot",
        back_populates="appointment",
        lazy="selectin",
    )
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="appointments",
        lazy="selectin",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="appointment",
        uselist=False,
        lazy="selectin",
    )
