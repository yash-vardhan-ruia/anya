"""
CareVoice AI Hospital Platform - Admin User Model.

Represents an administrative user with role-based access control
for the hospital management dashboard.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AdminRole
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog


class AdminUser(UUIDMixin, TimestampMixin, Base):
    """Administrative user for the hospital management platform.

    Attributes:
        email: Unique login email address.
        hashed_password: Bcrypt-hashed password.
        full_name: Admin's full name.
        role: Access control role (super_admin, admin, staff).
        is_active: Whether the account is active and can log in.
    """

    __tablename__ = "admin_users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        String(20),
        default=AdminRole.ADMIN,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Relationships ---
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="admin",
        lazy="selectin",
    )
