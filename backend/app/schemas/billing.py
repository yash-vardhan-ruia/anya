"""
CareVoice AI Hospital Platform - Billing Schemas.

Pydantic models for invoices and financial tracking.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from app.schemas.patient import PatientResponse


class InvoiceBase(BaseModel):
    invoice_number: str
    subtotal: int = Field(..., description="Amount in paise before GST")
    gst_rate: float = Field(..., description="GST percentage (e.g. 18.0)")
    gst_amount: int = Field(..., description="GST amount in paise")
    total_amount: int = Field(..., description="Total amount in paise")


class InvoiceCreate(BaseModel):
    """Schema to create a new invoice."""
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    subtotal: int
    gst_rate: float = 18.0


from datetime import date, datetime

class InvoiceResponse(InvoiceBase):
    """Response containing basic invoice details."""
    id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str | None = None
    appointment_date: date | None = None
    doctor_name: str | None = None
    department_name: str | None = None
    status: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """List of invoices."""
    total: int
    items: list[InvoiceResponse]


# Circular reference avoidance: import inline or use lazy relationships
class InvoiceDetailResponse(InvoiceResponse):
    """Response containing detailed invoice including preloaded relationships."""
    patient: PatientResponse | None = None
    appointment_id: uuid.UUID

    class Config:
        from_attributes = True
