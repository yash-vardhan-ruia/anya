"""
CareVoice AI Hospital Platform - Payment Schemas.

Pydantic models for Razorpay order creation and payment verification.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, Field
from app.core.constants import PaymentStatus


class PaymentCreateRequest(BaseModel):
    """Payload to initiate a payment order via Razorpay."""
    invoice_id: uuid.UUID


class PaymentOrderResponse(BaseModel):
    """Response containing created Razorpay order details for checkout."""
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    amount: float = Field(..., description="Amount in Rupees")
    razorpay_order_id: str
    razorpay_key_id: str
    status: PaymentStatus


class PaymentVerifyRequest(BaseModel):
    """Payload to verify Razorpay signature and capture payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    """Payment transaction details response."""
    id: uuid.UUID
    invoice_id: uuid.UUID
    patient_id: uuid.UUID
    amount: float
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """List of payment transactions."""
    total: int
    items: list[PaymentResponse]
