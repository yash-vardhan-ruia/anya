"""
CareVoice AI Hospital Platform - Appointment Schemas.

Pydantic models for appointment booking and management.
"""

from datetime import date, datetime, time
import uuid
from pydantic import BaseModel, Field
from app.core.constants import AppointmentStatus
from app.schemas.patient import PatientResponse
from app.schemas.doctor import DoctorResponse
from app.schemas.department import DepartmentResponse


class AppointmentBase(BaseModel):
    appointment_date: date
    start_time: time
    end_time: time
    status: AppointmentStatus = AppointmentStatus.PENDING
    symptoms: str | None = None
    notes: str | None = None


class AppointmentCreate(BaseModel):
    """Schema to create a new appointment."""
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    slot_id: uuid.UUID
    department_id: uuid.UUID
    appointment_date: date
    start_time: time
    end_time: time
    symptoms: str | None = None
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    """Schema to update an appointment."""
    status: AppointmentStatus | None = None
    symptoms: str | None = None
    notes: str | None = None


class AppointmentResponse(AppointmentBase):
    """Response schema containing appointment details."""
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    slot_id: uuid.UUID
    department_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    patient_name: str | None = None
    doctor_name: str | None = None
    doctor_specialization: str | None = None

    # Preloaded relationships as optional to avoid cycles/heavy loads
    patient: PatientResponse | None = None
    doctor: DoctorResponse | None = None
    department: DepartmentResponse | None = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """List of appointments."""
    total: int
    items: list[AppointmentResponse]
