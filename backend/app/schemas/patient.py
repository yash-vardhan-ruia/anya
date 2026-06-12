"""
CareVoice AI Hospital Platform - Patient Schemas.

Pydantic models for patient data operations.
"""

from datetime import date, datetime
import uuid
from pydantic import BaseModel, EmailStr, Field


class PatientBase(BaseModel):
    phone: str = Field(..., description="Unique contact phone number")
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr | None = None
    date_of_birth: date | None = None
    gender: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=500)


class PatientCreate(PatientBase):
    """Schema for creating a patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating patient demographics."""
    phone: str | None = None
    full_name: str | None = None
    email: EmailStr | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    address: str | None = None


class PatientResponse(PatientBase):
    """Response containing patient record details."""
    id: uuid.UUID
    medical_record_number: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Paginated or standard list of patients."""
    total: int
    items: list[PatientResponse]
