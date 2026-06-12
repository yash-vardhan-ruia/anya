"""
CareVoice AI Hospital Platform - Models Package.

Imports all SQLAlchemy models to ensure they are registered with the
DeclarativeBase metadata. This is required for Alembic migrations
and relationship resolution.
"""

from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.call_session import CallSession
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.emergency_incident import EmergencyIncident
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.payment import Payment
from app.models.schedule import DoctorSchedule
from app.models.slot import DoctorSlot

__all__ = [
    "AdminUser",
    "Appointment",
    "AuditLog",
    "Base",
    "CallSession",
    "Department",
    "Doctor",
    "DoctorSchedule",
    "DoctorSlot",
    "EmergencyIncident",
    "Invoice",
    "Notification",
    "Patient",
    "Payment",
]
