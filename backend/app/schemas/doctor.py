"""
CareVoice AI Hospital Platform - Doctor & Slot Schemas.

Pydantic models for doctors, schedules, and bookable slots.
"""

from datetime import date, datetime, time
import uuid
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import SlotStatus


class DoctorBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    specialization: str = Field(..., max_length=255)
    qualification: str = Field(..., max_length=500)
    experience_years: int = Field(..., ge=0)
    consultation_fee: int = Field(..., ge=0, description="Fee in paise (INR * 100)")
    phone: str = Field(..., max_length=20)
    email: EmailStr | None = None
    is_active: bool = True


class DoctorCreate(DoctorBase):
    """Schema to create a doctor."""
    department_id: uuid.UUID


class DoctorUpdate(BaseModel):
    """Schema to update a doctor."""
    department_id: uuid.UUID | None = None
    full_name: str | None = None
    specialization: str | None = None
    qualification: str | None = None
    experience_years: int | None = None
    consultation_fee: int | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


# --- Schedules ---

class DoctorScheduleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(30, ge=5, le=180)
    is_active: bool = True


class DoctorScheduleCreate(DoctorScheduleBase):
    """Schema to create a recurring schedule."""
    doctor_id: uuid.UUID


class DoctorScheduleResponse(DoctorScheduleBase):
    """Response containing doctor schedule template."""
    id: uuid.UUID
    doctor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorResponse(DoctorBase):
    """Response containing doctor details."""
    id: uuid.UUID
    department_id: uuid.UUID
    department_name: str | None = None
    schedules: list[DoctorScheduleResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorListResponse(BaseModel):
    """Paginated list of doctors."""
    total: int
    items: list[DoctorResponse]


# --- Slots ---

class SlotResponse(BaseModel):
    """Response containing doctor slot details."""
    id: uuid.UUID
    doctor_id: uuid.UUID
    schedule_id: uuid.UUID
    date: date
    start_time: time
    end_time: time
    status: SlotStatus
    locked_until: datetime | None = None
    locked_by: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SlotListResponse(BaseModel):
    """List of slots."""
    total: int
    items: list[SlotResponse]
