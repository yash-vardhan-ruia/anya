"""
CareVoice AI Hospital Platform - Doctor Slot Model.

Represents a concrete, bookable time slot for a doctor on a specific date.
Supports locking to prevent double-booking during concurrent call sessions.
"""

import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SlotStatus
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import Doctor
    from app.models.schedule import DoctorSchedule


class DoctorSlot(UUIDMixin, TimestampMixin, Base):
    """Concrete time slot for a specific doctor on a specific date.

    Supports optimistic locking via locked_until and locked_by to
    prevent double-booking during concurrent AI voice call sessions.

    Attributes:
        doctor_id: FK to the doctor.
        schedule_id: FK to the schedule template that generated this slot.
        date: The calendar date of the slot.
        start_time: Slot start time.
        end_time: Slot end time.
        status: Current slot status (available, locked, booked).
        locked_until: Timestamp until which the slot is reserved.
        locked_by: Identifier of the session/user that locked the slot.
    """

    __tablename__ = "doctor_slots"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctor_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[SlotStatus] = mapped_column(
        String(20),
        default=SlotStatus.AVAILABLE,
        nullable=False,
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    locked_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_slot_datetime"),
    )

    # --- Relationships ---
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="slots",
        lazy="selectin",
    )
    schedule: Mapped["DoctorSchedule"] = relationship(
        "DoctorSchedule",
        back_populates="slots",
        lazy="selectin",
    )
    appointment: Mapped["Appointment | None"] = relationship(
        "Appointment",
        back_populates="slot",
        uselist=False,
        lazy="selectin",
    )
