"""
CareVoice AI Hospital Platform - Domain Constants & Enumerations.

Defines all status enums and domain constants used across the platform.
"""

from enum import Enum


class SlotStatus(str, Enum):
    """Status of a doctor's time slot."""

    AVAILABLE = "available"
    LOCKED = "locked"
    BOOKED = "booked"


class AppointmentStatus(str, Enum):
    """Lifecycle status of an appointment."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    """Status of a payment transaction."""

    PENDING = "pending"
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class CallStatus(str, Enum):
    """Status of a Twilio voice call session."""

    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AdminRole(str, Enum):
    """Role-based access levels for admin users."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STAFF = "staff"


class ConversationState(str, Enum):
    """State machine states for the AI voice conversation flow."""

    GREETING = "greeting"
    IDENTITY = "identity"
    SYMPTOMS = "symptoms"
    DEPT = "dept"
    DOCTOR = "doctor"
    SLOT = "slot"
    REVIEW = "review"
    PAYMENT = "payment"
    CONFIRM = "confirm"
    COMPLETE = "complete"


class EmergencySeverity(str, Enum):
    """Severity classification for emergency incidents."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
