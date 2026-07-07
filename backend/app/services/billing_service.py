"""
CareVoice AI Hospital Platform - Billing Service.

Handles calculating consultation fees, applying GST, generating unique invoices,
and looking up detailed financial invoice summaries.
"""

import datetime
import secrets
import uuid
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import settings
from app.models.invoice import Invoice
from app.models.appointment import Appointment

logger = structlog.get_logger(__name__)


class BillingService:
    """Business logic for billing, GST calculations, and invoice management."""

    @staticmethod
    def _generate_invoice_number() -> str:
        """Generate a unique billing invoice number."""
        today_str = datetime.date.today().strftime("%Y%m%d")
        rand_suffix = "".join(secrets.choice("0123456789") for _ in range(4))
        return f"INV-{today_str}-{rand_suffix}"

    @classmethod
    async def get_invoice(cls, db: AsyncSession, invoice_id: uuid.UUID) -> Invoice | None:
        """Retrieve an invoice by its UUID."""
        return await db.get(Invoice, invoice_id)

    @classmethod
    async def get_invoice_by_appointment(cls, db: AsyncSession, appointment_id: uuid.UUID) -> Invoice | None:
        """Retrieve the invoice associated with a specific appointment."""
        stmt = select(Invoice).where(Invoice.appointment_id == appointment_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_invoice(cls, db: AsyncSession, appointment_id: uuid.UUID) -> Invoice:
        """Calculate costs and generate a new Invoice for an appointment.

        GST is calculated at the rate configured in settings.GST_RATE (default 18.0%).
        """
        # Fetch existing invoice to prevent duplicates
        existing = await cls.get_invoice_by_appointment(db, appointment_id)
        if existing:
            logger.info("Invoice already exists for appointment", appointment_id=str(appointment_id), invoice_id=str(existing.id))
            return existing

        # Fetch appointment details (with doctor details preloaded)
        stmt = select(Appointment).options(selectinload(Appointment.doctor)).where(Appointment.id == appointment_id)
        appointment = (await db.execute(stmt)).scalar_one_or_none()
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found.")

        # Subtotal is the doctor's consultation fee (already in INR Rupees)
        subtotal = float(appointment.doctor.consultation_fee)
        gst_rate = settings.GST_RATE
        gst_amount = round(subtotal * (gst_rate / 100.0), 2)
        total_amount = round(subtotal + gst_amount, 2)

        # Generate unique invoice number
        attempts = 0
        max_attempts = 10
        invoice_num = cls._generate_invoice_number()
        while attempts < max_attempts:
            stmt = select(Invoice).where(Invoice.invoice_number == invoice_num)
            dup = (await db.execute(stmt)).scalar_one_or_none()
            if not dup:
                break
            invoice_num = cls._generate_invoice_number()
            attempts += 1
        else:
            raise RuntimeError("Failed to generate a unique invoice number after 10 attempts.")

        invoice = Invoice(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            invoice_number=invoice_num,
            subtotal=subtotal,
            gst_rate=gst_rate,
            gst_amount=gst_amount,
            total_amount=total_amount,
        )
        db.add(invoice)
        await db.flush()  # Populates invoice.id
        
        logger.info("Generated new invoice", invoice_number=invoice_num, total_amount=total_amount, invoice_id=str(invoice.id))
        return invoice

    @classmethod
    async def list_invoices(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        patient_id: uuid.UUID | None = None,
    ) -> tuple[int, list[Invoice]]:
        """List invoices, optionally filtered by patient."""
        stmt = select(Invoice)
        if patient_id:
            stmt = stmt.where(Invoice.patient_id == patient_id)

        count_stmt = select(func.count(Invoice.id))
        if patient_id:
            count_stmt = count_stmt.where(Invoice.patient_id == patient_id)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Invoice.created_at.desc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items
