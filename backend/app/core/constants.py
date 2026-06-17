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
    """Status of a voice call session."""

    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AdminRole(str, Enum):
    """Role-based access levels for admin users."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"


class ConversationState(str, Enum):
    """
    State machine states for the AI voice conversation flow.

    Hybrid voice + browser model:
    - Voice handles natural conversation
    - Browser handles precision inputs (email, doctor pick, slot pick, payment)
    """

    # Anya greets and asks new or returning patient
    GREETING = "greeting"

    # Waiting for patient type answer ("new" / "returning")
    TYPE_CHECK = "type_check"

    # Collecting name, age, gender from new patient (voice)
    # Email is collected via browser text input
    NEW_INFO = "new_info"

    # Returning patient: browser shows email input → check_patient_by_email
    RETURNING_LOOKUP = "returning_lookup"

    # Asking for symptoms / reason for visit (voice)
    SYMPTOMS = "symptoms"

    # Suggesting department and confirming (voice)
    DEPT_ROUTING = "dept_routing"

    # Browser shows doctor cards → patient clicks one
    DOCTOR_SELECT = "doctor_select"

    # Browser shows slot cards → patient clicks one
    SLOT_SELECT = "slot_select"

    # Anya reads back all details, asks for verbal confirmation
    BOOKING_REVIEW = "booking_review"

    # Payment link sent, Anya says goodbye → call auto-ends
    FAREWELL = "farewell"

    # Session complete
    COMPLETE = "complete"


class EmergencySeverity(str, Enum):
    """Severity classification for emergency incidents."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
