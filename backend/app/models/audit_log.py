"""
CareVoice AI Hospital Platform - Audit Log Model.

Immutable audit trail for all administrative actions performed
in the hospital management dashboard.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser


class AuditLog(UUIDMixin, Base):
    """Immutable audit log entry for admin actions.

    Records who did what, to which entity, with optional details
    and the IP address of the request.

    Attributes:
        admin_id: FK to the admin user who performed the action (nullable for system actions).
        action: Action performed (e.g., 'create', 'update', 'delete', 'login').
        entity_type: Type of entity affected (e.g., 'doctor', 'appointment').
        entity_id: ID of the affected entity as a string.
        details: Optional JSON payload with additional context about the change.
        ip_address: IP address from which the action was performed.
        created_at: Timestamp of the action.
    """

    __tablename__ = "audit_logs"

    admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    admin: Mapped["AdminUser | None"] = relationship(
        "AdminUser",
        back_populates="audit_logs",
        lazy="selectin",
    )
