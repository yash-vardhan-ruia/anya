"""
CareVoice AI Hospital Platform - Department Model.

Represents a hospital department (e.g., Cardiology, Orthopedics).
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.doctor import Doctor


class Department(UUIDMixin, TimestampMixin, Base):
    """Hospital department entity.

    Attributes:
        name: Unique department name.
        description: Optional description of the department.
        is_active: Whether the department is currently operational.
    """

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    doctors: Mapped[list["Doctor"]] = relationship(
        "Doctor",
        back_populates="department",
        lazy="selectin",
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment",
        back_populates="department",
        lazy="selectin",
    )
