"""
CareVoice AI Hospital Platform - Payment Model.

Represents a Razorpay payment linked to an invoice,
tracking the full payment lifecycle.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PaymentStatus
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.patient import Patient


class Payment(UUIDMixin, TimestampMixin, Base):
    """Payment transaction linked to an invoice via Razorpay.

    All monetary amounts are stored in paise (1 INR = 100 paise).

    Attributes:
        invoice_id: FK to the invoice (one payment per invoice).
        patient_id: FK to the patient making the payment.
        amount: Payment amount in paise.
        razorpay_order_id: Razorpay order ID.
        razorpay_payment_id: Razorpay payment ID (set after payment).
        razorpay_signature: Razorpay signature for verification.
        status: Current payment lifecycle status.
    """

    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    razorpay_signature: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        default=PaymentStatus.PENDING,
        nullable=False,
    )

    # --- Relationships ---
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="payment",
        lazy="selectin",
    )
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="payments",
        lazy="selectin",
    )
