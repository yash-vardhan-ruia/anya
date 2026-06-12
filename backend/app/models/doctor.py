"""
CareVoice AI Hospital Platform - Doctor Model.

Represents a doctor in the hospital with department affiliation,
qualifications, and consultation fee.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.department import Department
    from app.models.schedule import DoctorSchedule
    from app.models.slot import DoctorSlot


class Doctor(UUIDMixin, TimestampMixin, Base):
    """Doctor entity with professional details and department link.

    Attributes:
        department_id: FK to the department this doctor belongs to.
        full_name: Doctor's full name.
        specialization: Area of medical specialization.
        qualification: Medical degree/qualification string.
        experience_years: Years of professional experience.
        consultation_fee: Consultation fee in paise (INR * 100).
        phone: Contact phone number.
        email: Optional contact email.
        is_active: Whether the doctor is currently accepting patients.
    """

    __tablename__ = "doctors"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), nullable=False)
    qualification: Mapped[str] = mapped_column(String(500), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    consultation_fee: Mapped[int] = mapped_column(Integer, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    department: Mapped["Department"] = relationship(
        "Department",
        back_populates="doctors",
        lazy="selectin",
    )
    schedules: Mapped[list["DoctorSchedule"]] = relationship(
        "DoctorSchedule",
        back_populates="doctor",
        lazy="selectin",
    )
    slots: Mapped[list["DoctorSlot"]] = relationship(
        "DoctorSlot",
        back_populates="doctor",
        lazy="selectin",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="doctor",
        lazy="selectin",
    )

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

