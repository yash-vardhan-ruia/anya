"""
CareVoice AI Hospital Platform - Pydantic Schemas Package.

Exposes all schemas used for API request/response validation.
"""

from app.schemas.auth import (
    AdminCreate,
    AdminResponse,
    LoginRequest,
    TokenResponse,
)
from app.schemas.patient import (
    PatientCreate,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.schemas.doctor import (
    DoctorCreate,
    DoctorListResponse,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
    DoctorUpdate,
    SlotListResponse,
    SlotResponse,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.schemas.billing import (
    InvoiceCreate,
    InvoiceDetailResponse,
    InvoiceListResponse,
    InvoiceResponse,
)
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentOrderResponse,
    PaymentResponse,
    PaymentVerifyRequest,
)
from app.schemas.analytics import (
    AnalyticsResponse,
    CallAnalytics,
    DashboardStats,
    DepartmentMetrics,
)

__all__ = [
    "AdminCreate",
    "AdminResponse",
    "LoginRequest",
    "TokenResponse",
    "PatientCreate",
    "PatientListResponse",
    "PatientResponse",
    "PatientUpdate",
    "DoctorCreate",
    "DoctorListResponse",
    "DoctorResponse",
    "DoctorScheduleCreate",
    "DoctorScheduleResponse",
    "DoctorUpdate",
    "SlotListResponse",
    "SlotResponse",
    "DepartmentCreate",
    "DepartmentListResponse",
    "DepartmentResponse",
    "DepartmentUpdate",
    "AppointmentCreate",
    "AppointmentListResponse",
    "AppointmentResponse",
    "AppointmentUpdate",
    "InvoiceCreate",
    "InvoiceDetailResponse",
    "InvoiceListResponse",
    "InvoiceResponse",
    "PaymentCreateRequest",
    "PaymentListResponse",
    "PaymentOrderResponse",
    "PaymentResponse",
    "PaymentVerifyRequest",
    "AnalyticsResponse",
    "CallAnalytics",
    "DashboardStats",
    "DepartmentMetrics",
]
