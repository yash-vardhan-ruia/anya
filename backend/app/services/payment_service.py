"""
CareVoice AI Hospital Platform - Payment Service.

Orchestrates payment transaction lifecycles by interfacing with the RazorpayClient integration,
verifying signatures, and confirming appointments upon payment completion.
"""

import uuid
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.constants import PaymentStatus
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.integrations.razorpay_client import razorpay_client
from app.services.appointment_service import AppointmentService
from app.core.constants import PaymentStatus, ConversationState
from app.models.slot import DoctorSlot
from app.schemas.appointment import AppointmentCreate
from app.services.patient_service import PatientService
from app.services.billing_service import BillingService
from app.voice.session_manager import VoiceSessionManager

logger = structlog.get_logger(__name__)


class PaymentService:
    """Business logic for Razorpay orders and payment verification."""

    @classmethod
    async def get_payment(cls, db: AsyncSession, payment_id: uuid.UUID) -> Payment | None:
        """Retrieve a payment transaction by UUID."""
        return await db.get(Payment, payment_id)

    @classmethod
    async def get_payment_by_order_id(cls, db: AsyncSession, order_id: str) -> Payment | None:
        """Find a payment record by its unique Razorpay order ID."""
        stmt = select(Payment).where(Payment.razorpay_order_id == order_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_payment_order(cls, db: AsyncSession, invoice_id: uuid.UUID) -> Payment:
        """Initiate a Razorpay payment order for an existing invoice.

        Reuses an existing created order or generates a new one.
        """
        # Fetch the invoice
        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found.")

        # Check for existing payment details
        stmt = select(Payment).where(Payment.invoice_id == invoice_id)
        existing_payment_result = await db.execute(stmt)
        existing_payment = existing_payment_result.scalar_one_or_none()

        if existing_payment:
            if existing_payment.status == PaymentStatus.CAPTURED:
                raise ValueError("This invoice has already been paid.")
            # If a pending or failed payment order exists, we can create a fresh order to retry
            logger.info("Retrying payment for invoice", invoice_id=str(invoice_id), old_order_id=existing_payment.razorpay_order_id)

        # Call Razorpay client to create an order
        razorpay_order = razorpay_client.create_order(
            amount_paise=invoice.total_amount,
            receipt_id=str(invoice.id)
        )
        
        order_id = razorpay_order.get("id")

        if existing_payment:
            # Update existing record
            existing_payment.razorpay_order_id = order_id
            existing_payment.status = PaymentStatus.CREATED
            payment_record = existing_payment
        else:
            # Create a brand new record
            payment_record = Payment(
                invoice_id=invoice_id,
                patient_id=invoice.patient_id,
                amount=invoice.total_amount,
                razorpay_order_id=order_id,
                status=PaymentStatus.CREATED,
            )
            db.add(payment_record)

        await db.commit()
        await db.refresh(payment_record)
        logger.info("Razorpay order linked to Payment record", payment_id=str(payment_record.id), order_id=order_id)
        return payment_record

    @classmethod
    async def verify_payment(
        cls,
        db: AsyncSession,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify the Razorpay payment signature and finalize the appointment schedule."""
        payment = await cls.get_payment_by_order_id(db, razorpay_order_id)
        if not payment:
            logger.error("No payment record found matching Razorpay order ID", order_id=razorpay_order_id)
            return False

        if payment.status == PaymentStatus.CAPTURED:
            logger.info("Payment already captured, skipping signature verification", order_id=razorpay_order_id)
            return True

        # Perform signature verification
        is_valid = razorpay_client.verify_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )

        if is_valid:
            # 1. Update payment details
            payment.status = PaymentStatus.CAPTURED
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            
            # 2. Confirm the corresponding appointment
            invoice = payment.invoice
            if invoice:
                await AppointmentService.confirm_appointment(db, invoice.appointment_id)
                logger.info("Payment verified. Confirming appointment.", appointment_id=str(invoice.appointment_id))
            
            await db.commit()
            logger.info("Payment signature verified successfully", payment_id=str(payment.id), order_id=razorpay_order_id)
            return True
        else:
            # Update payment details to failed
            payment.status = PaymentStatus.FAILED
            await db.commit()
            logger.warning("Payment signature verification failed", payment_id=str(payment.id), order_id=razorpay_order_id)
            return False

        @classmethod
        async def handle_webhook_event(cls, db: AsyncSession, event: dict) -> None:
            """Handle Razorpay webhook events.

            New payment-link flow:
            payment_link.paid -> read Redis booking session -> create patient,
            appointment, invoice, payment record -> clear Redis.
            """
            event_type = event.get("event")

            if event_type == "payment_link.paid":
                payment_link_entity = (
                    event.get("payload", {})
                    .get("payment_link", {})
                    .get("entity", {})
                )

                payment_entity = (
                    event.get("payload", {})
                    .get("payment", {})
                    .get("entity", {})
                )

                notes = payment_link_entity.get("notes") or {}
                session_id = notes.get("session_id")

                payment_link_id = payment_link_entity.get("id")
                payment_link_url = payment_link_entity.get("short_url")
                amount = payment_link_entity.get("amount") or payment_entity.get("amount")
                razorpay_payment_id = payment_entity.get("id")

                if not session_id:
                    logger.error("payment_link.paid webhook missing session_id in notes")
                    return

                session = await VoiceSessionManager.get_session(session_id)

                if not session:
                    logger.error("No Redis voice session found for paid payment link", session_id=session_id)
                    return

                patient_name = session.get("patient_name")
                phone = session.get("phone")
                symptoms = session.get("symptoms")
                slot_id = session.get("slot_id")

                if not patient_name or not phone or not slot_id:
                    logger.error(
                        "Redis session missing required booking details",
                        session_id=session_id,
                        patient_name=patient_name,
                        phone=phone,
                        slot_id=slot_id,
                    )
                    return

                slot = await db.get(DoctorSlot, uuid.UUID(slot_id))
                if not slot:
                    logger.error("Slot not found while creating appointment after payment", slot_id=slot_id)
                    return

                patient = await PatientService.get_or_create_patient_by_phone(
                    db=db,
                    phone=phone,
                    full_name=patient_name,
                )

                appointment_schema = AppointmentCreate(
                    patient_id=patient.id,
                    doctor_id=slot.doctor_id,
                    slot_id=slot.id,
                    department_id=slot.doctor.department_id,
                    appointment_date=slot.date,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    symptoms=symptoms,
                    notes=f"Paid via Razorpay Payment Link {payment_link_id}. Voice session {session_id}.",
                )

                appointment = await AppointmentService.create_appointment(
                    db=db,
                    schema=appointment_schema,
                    locked_by_session=session_id,
                )

                appointment = await AppointmentService.confirm_appointment(
                    db=db,
                    appointment_id=appointment.id,
                )

                invoice = await BillingService.get_invoice_by_appointment(
                    db=db,
                    appointment_id=appointment.id,
                )

                if invoice:
                    existing_payment_stmt = select(Payment).where(Payment.invoice_id == invoice.id)
                    existing_payment = (await db.execute(existing_payment_stmt)).scalar_one_or_none()

                    if not existing_payment:
                        payment_record = Payment(
                            invoice_id=invoice.id,
                            patient_id=patient.id,
                            amount=amount or invoice.total_amount,
                            razorpay_order_id=payment_link_id,
                            razorpay_payment_id=razorpay_payment_id,
                            status=PaymentStatus.CAPTURED,
                        )
                        db.add(payment_record)
                    else:
                        existing_payment.status = PaymentStatus.CAPTURED
                        existing_payment.razorpay_order_id = payment_link_id
                        existing_payment.razorpay_payment_id = razorpay_payment_id

                    await db.commit()

                await VoiceSessionManager.update_session(
                    session_id,
                    {
                        "current_state": ConversationState.COMPLETE.value,
                        "patient_id": str(patient.id),
                        "appointment_id": str(appointment.id),
                        "invoice_id": str(invoice.id) if invoice else None,
                        "payment_status": "captured",
                    },
                )

                # If your session manager has delete_session(), use that.
                if hasattr(VoiceSessionManager, "delete_session"):
                    await VoiceSessionManager.delete_session(session_id)

                logger.info(
                    "Payment link paid. Appointment created and Redis session cleared.",
                    session_id=session_id,
                    appointment_id=str(appointment.id),
                    patient_id=str(patient.id),
                    payment_link_id=payment_link_id,
                )
                return

            if event_type == "payment.captured":
                payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
                order_id = payment_entity.get("order_id")
                payment_id = payment_entity.get("id")
                signature = event.get("signature", "")

                if order_id and payment_id:
                    logger.info("Processing webhook payment.captured", order_id=order_id, payment_id=payment_id)
                    payment = await cls.get_payment_by_order_id(db, order_id)
                    if payment and payment.status != PaymentStatus.CAPTURED:
                        payment.status = PaymentStatus.CAPTURED
                        payment.razorpay_payment_id = payment_id
                        payment.razorpay_signature = signature

                        invoice = payment.invoice
                        if invoice:
                            await AppointmentService.confirm_appointment(db, invoice.appointment_id)
                            logger.info("Webhook updated appointment to CONFIRMED", appointment_id=str(invoice.appointment_id))

                        await db.commit()
                        logger.info("Webhook processed successfully for order_id", order_id=order_id)
                return

            logger.info("Skipping webhook event type", event_type=event_type)

        


    @classmethod
    async def list_payments(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: PaymentStatus | None = None,
    ) -> tuple[int, list[Payment]]:
        """List payment transactions with optional filters."""
        stmt = select(Payment)
        if status:
            stmt = stmt.where(Payment.status == status)

        count_stmt = select(func.count(Payment.id))
        if status:
            count_stmt = count_stmt.where(Payment.status == status)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Payment.created_at.desc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items

