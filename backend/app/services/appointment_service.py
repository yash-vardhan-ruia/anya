"""
CareVoice AI Hospital Platform - Appointment Service.

Handles scheduling appointments, verifying slot states, transitions,
integrating invoice generation, and triggering Celery background tasks.
"""

import uuid
import datetime
import structlog
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AppointmentStatus, SlotStatus
from app.models.appointment import Appointment
from app.models.slot import DoctorSlot
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.billing_service import BillingService

logger = structlog.get_logger(__name__)


class AppointmentService:
    """Business logic for booking and managing patient appointments."""

    @classmethod
    async def get_appointment(cls, db: AsyncSession, appointment_id: uuid.UUID) -> Appointment | None:
        """Retrieve an appointment by ID."""
        return await db.get(Appointment, appointment_id)

    @classmethod
    async def create_appointment(
        cls,
        db: AsyncSession,
        schema: AppointmentCreate,
        locked_by_session: str | None = None,
    ) -> Appointment:
        """Book a new appointment, transition slot to BOOKED, and create a pending invoice.

        Also dispatches a Celery task for notifications.
        """
        # 1. Fetch and verify slot
        slot = await db.get(DoctorSlot, schema.slot_id)
        if not slot:
            raise ValueError("Doctor slot not found.")

        if slot.doctor_id != schema.doctor_id:
            raise ValueError("Doctor ID mismatch for the selected slot.")

        if slot.status == SlotStatus.BOOKED:
            raise ValueError("This time slot has already been booked.")

        # Check patient double-booking for the same date and time
        overlap_stmt = select(func.count(Appointment.id)).where(
            and_(
                Appointment.patient_id == schema.patient_id,
                Appointment.appointment_date == schema.appointment_date,
                Appointment.start_time == schema.start_time,
                Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
            )
        )
        overlap_count = (await db.execute(overlap_stmt)).scalar_one() or 0
        if overlap_count > 0:
            raise ValueError("Patient already has an appointment scheduled at this time.")

        # If locked_by_session is provided, confirm the lock is held by the same caller session
        now_tz = datetime.datetime.now(datetime.timezone.utc)
        if slot.status == SlotStatus.LOCKED and slot.locked_until and slot.locked_until > now_tz:
            if locked_by_session and slot.locked_by != locked_by_session:
                raise ValueError("This slot is locked by another session. Please select another time.")

        # 2. Transition slot status to BOOKED
        slot.status = SlotStatus.BOOKED
        slot.locked_until = None
        slot.locked_by = None

        # 3. Create appointment (defaults to PENDING until payment is verified or confirmed)
        appointment = Appointment(
            patient_id=schema.patient_id,
            doctor_id=schema.doctor_id,
            slot_id=schema.slot_id,
            department_id=schema.department_id,
            appointment_date=schema.appointment_date,
            start_time=schema.start_time,
            end_time=schema.end_time,
            status=AppointmentStatus.PENDING,
            symptoms=schema.symptoms,
            notes=schema.notes,
        )
        db.add(appointment)
        await db.flush()  # Populates appointment.id

        # 4. Generate invoice automatically (using BillingService)
        # Note: BillingService computes consultation fee and GST
        invoice = await BillingService.create_invoice(db, appointment.id)

        await db.commit()
        await db.refresh(appointment)
        logger.info(
            "Created appointment & pending invoice",
            appointment_id=str(appointment.id),
            invoice_id=str(invoice.id),
            patient_id=str(schema.patient_id)
        )

        # 5. Dispatch Celery task for notification (Import dynamically to avoid circular references)
        try:
            from app.tasks.notification_tasks import send_appointment_notifications
            send_appointment_notifications.delay(str(appointment.id), "created")
            logger.info("Dispatched notification task to Celery", appointment_id=str(appointment.id))
        except Exception as e:
            logger.error("Failed to dispatch Celery task directly; will retry in background", error=str(e))

        return appointment

    @classmethod
    async def confirm_appointment(cls, db: AsyncSession, appointment_id: uuid.UUID) -> Appointment | None:
        """Confirm an appointment (typically triggered by successful payment)."""
        appointment = await cls.get_appointment(db, appointment_id)
        if not appointment:
            return None

        if appointment.status == AppointmentStatus.CONFIRMED:
            return appointment

        appointment.status = AppointmentStatus.CONFIRMED
        await db.commit()
        logger.info("Appointment status updated to CONFIRMED", appointment_id=str(appointment_id))

        # Dispatch confirmation notification task
        try:
            from app.tasks.notification_tasks import send_appointment_notifications
            send_appointment_notifications.delay(str(appointment.id), "confirmed")
        except Exception as e:
            logger.error("Failed to dispatch Celery notification task", error=str(e))

        return appointment

    @classmethod
    async def cancel_appointment(
        cls, db: AsyncSession, appointment_id: uuid.UUID, reason: str | None = None
    ) -> Appointment | None:
        """Cancel an appointment and free up the corresponding doctor slot."""
        appointment = await cls.get_appointment(db, appointment_id)
        if not appointment:
            return None

        if appointment.status == AppointmentStatus.CANCELLED:
            return appointment

        appointment.status = AppointmentStatus.CANCELLED
        if reason:
            appointment.notes = f"{appointment.notes or ''}\nCancellation Reason: {reason}".strip()

        # Free the slot
        if appointment.slot:
            appointment.slot.status = SlotStatus.AVAILABLE
            appointment.slot.locked_until = None
            appointment.slot.locked_by = None

        await db.commit()
        logger.info("Appointment status updated to CANCELLED", appointment_id=str(appointment_id))

        # Dispatch cancellation notification task
        try:
            from app.tasks.notification_tasks import send_appointment_notifications
            send_appointment_notifications.delay(str(appointment.id), "cancelled")
        except Exception as e:
            logger.error("Failed to dispatch Celery notification task", error=str(e))

        return appointment

    @classmethod
    async def update_appointment(
        cls, db: AsyncSession, appointment_id: uuid.UUID, schema: AppointmentUpdate
    ) -> Appointment | None:
        """Update an existing appointment's details (status, symptoms, notes)."""
        appointment = await cls.get_appointment(db, appointment_id)
        if not appointment:
            return None

        if schema.status is not None:
            # If transitioning to CANCELLED, handle the slot freeing logic
            if schema.status == AppointmentStatus.CANCELLED and appointment.status != AppointmentStatus.CANCELLED:
                if appointment.slot:
                    appointment.slot.status = SlotStatus.AVAILABLE
                    appointment.slot.locked_until = None
                    appointment.slot.locked_by = None
            appointment.status = schema.status

        if schema.symptoms is not None:
            appointment.symptoms = schema.symptoms

        if schema.notes is not None:
            appointment.notes = schema.notes

        await db.commit()
        logger.info("Updated appointment details", appointment_id=str(appointment_id))
        return appointment

    @classmethod
    async def list_appointments(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        patient_id: uuid.UUID | None = None,
        doctor_id: uuid.UUID | None = None,
        date_filter: datetime.date | None = None,
        status: AppointmentStatus | None = None,
    ) -> tuple[int, list[Appointment]]:
        """List appointments with filters."""
        stmt = select(Appointment)
        if patient_id:
            stmt = stmt.where(Appointment.patient_id == patient_id)
        if doctor_id:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
        if date_filter:
            stmt = stmt.where(Appointment.appointment_date == date_filter)
        if status:
            stmt = stmt.where(Appointment.status == status)

        # Count query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items
