"""
CareVoice AI Hospital Platform - Doctor Schedule Model.

Represents a recurring weekly schedule template for a doctor,
defining which days and time blocks they are available.
"""

import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.doctor import Doctor
    from app.models.slot import DoctorSlot


class DoctorSchedule(UUIDMixin, TimestampMixin, Base):
    """Recurring weekly schedule for a doctor.

    Attributes:
        doctor_id: FK to the doctor who owns this schedule.
        day_of_week: Day of the week (0=Monday, 6=Sunday).
        start_time: Start time of the availability window.
        end_time: End time of the availability window.
        slot_duration_minutes: Length of each appointment slot in minutes.
        is_active: Whether this schedule is currently active.
    """

    __tablename__ = "doctor_schedules"

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    doctor: Mapped["Doctor"] = relationship(
        "Doctor",
        back_populates="schedules",
        lazy="selectin",
    )
    slots: Mapped[list["DoctorSlot"]] = relationship(
        "DoctorSlot",
        back_populates="schedule",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
