"""
CareVoice AI Hospital Platform - Doctor Slot Service.

Manages calendar slots for doctors, including dynamic generation from weekly schedules,
retrieval of available slots, and highly concurrent Redis/DB-backed slot locking to prevent double bookings.
"""

import datetime
import uuid
import redis.asyncio as aioredis
import structlog
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.constants import SlotStatus
from app.models.slot import DoctorSlot
from app.models.schedule import DoctorSchedule

logger = structlog.get_logger(__name__)

# Initialize async Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class SlotService:
    """Business logic for Doctor Slot management and concurrent locking."""

    @classmethod
    async def generate_slots_for_doctor(
        cls,
        db: AsyncSession,
        doctor_id: uuid.UUID,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> int:
        """Generate concrete DoctorSlot records from recurring DoctorSchedule templates.

        Args:
            db: Async database session
            doctor_id: Doctor identifier
            start_date: Begin generating from this date
            end_date: End generating on this date (inclusive)

        Returns:
            int: Number of slots successfully generated
        """
        # Fetch active schedules for this doctor
        stmt = select(DoctorSchedule).where(
            and_(
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.is_active == True,
            )
        )
        schedules_result = await db.execute(stmt)
        schedules = list(schedules_result.scalars().all())

        if not schedules:
            logger.warning("No active schedules found for doctor, skipping slot generation", doctor_id=str(doctor_id))
            return 0

        slots_created = 0
        current_date = start_date
        one_day = datetime.timedelta(days=1)

        while current_date <= end_date:
            # Python weekday() returns 0=Monday, 6=Sunday
            weekday = current_date.weekday()
            
            # Find matching schedules for this weekday
            matching_schedules = [s for s in schedules if s.day_of_week == weekday]

            for schedule in matching_schedules:
                # Helper calculation using combined datetimes
                start_dt = datetime.datetime.combine(current_date, schedule.start_time)
                end_dt = datetime.datetime.combine(current_date, schedule.end_time)
                slot_duration = datetime.timedelta(minutes=schedule.slot_duration_minutes)

                temp_dt = start_dt
                while temp_dt + slot_duration <= end_dt:
                    slot_start = temp_dt.time()
                    slot_end = (temp_dt + slot_duration).time()

                    # Check if slot already exists to prevent integrity errors
                    exists_stmt = select(DoctorSlot).where(
                        and_(
                            DoctorSlot.doctor_id == doctor_id,
                            DoctorSlot.date == current_date,
                            DoctorSlot.start_time == slot_start,
                        )
                    )
                    exists_result = await db.execute(exists_stmt)
                    if exists_result.scalar_one_or_none():
                        temp_dt += slot_duration
                        continue

                    # Create concrete slot
                    new_slot = DoctorSlot(
                        doctor_id=doctor_id,
                        schedule_id=schedule.id,
                        date=current_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        status=SlotStatus.AVAILABLE,
                    )
                    db.add(new_slot)
                    slots_created += 1
                    temp_dt += slot_duration

            current_date += one_day

        await db.commit()
        logger.info(
            "Generated doctor slots from schedules",
            doctor_id=str(doctor_id),
            slots_count=slots_created,
            start=str(start_date),
            end=str(end_date)
        )
        return slots_created

    @classmethod
    async def list_available_slots(
        cls,
        db: AsyncSession,
        doctor_id: uuid.UUID,
        target_date: datetime.date,
    ) -> list[DoctorSlot]:
        """List slots for a doctor on a specific date that are either AVAILABLE or expired locks."""
        now_tz = datetime.datetime.now(datetime.timezone.utc)

        # Clear expired locks first in DB
        expired_stmt = select(DoctorSlot).where(
            and_(
                DoctorSlot.doctor_id == doctor_id,
                DoctorSlot.date == target_date,
                DoctorSlot.status == SlotStatus.LOCKED,
                DoctorSlot.locked_until < now_tz
            )
        )
        expired_result = await db.execute(expired_stmt)
        expired_slots = list(expired_result.scalars().all())
        for slot in expired_slots:
            slot.status = SlotStatus.AVAILABLE
            slot.locked_until = None
            slot.locked_by = None
        if expired_slots:
            await db.commit()

        # Fetch all available or validly open slots
        stmt = select(DoctorSlot).where(
            and_(
                DoctorSlot.doctor_id == doctor_id,
                DoctorSlot.date == target_date,
                or_(
                    DoctorSlot.status == SlotStatus.AVAILABLE,
                    and_(
                        DoctorSlot.status == SlotStatus.LOCKED,
                        DoctorSlot.locked_until < now_tz
                    )
                )
            )
        ).order_by(DoctorSlot.start_time.asc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def lock_slot(cls, db: AsyncSession, slot_id: uuid.UUID, locked_by: str) -> bool:
        """Lock a slot in both Redis and PostgreSQL to avoid concurrent booking conflicts.

        TTL is defined in settings.SLOT_LOCK_TTL_SECONDS (default 5 minutes).
        """
        redis_key = f"lock:slot:{slot_id}"
        ttl = settings.SLOT_LOCK_TTL_SECONDS

        try:
            # 1. Acquire Redis distributed lock
            acquired = await redis_client.set(redis_key, locked_by, ex=ttl, nx=True)
            if not acquired:
                logger.warning("Redis lock acquisition failed (slot already locked)", slot_id=str(slot_id))
                return False

            # 2. Query slot in database
            slot = await db.get(DoctorSlot, slot_id)
            if not slot:
                await redis_client.delete(redis_key)
                return False

            now_tz = datetime.datetime.now(datetime.timezone.utc)

            # A slot can be locked if:
            # - status is AVAILABLE
            # - status is LOCKED but the lock timestamp has expired
            can_lock = (
                slot.status == SlotStatus.AVAILABLE or
                (slot.status == SlotStatus.LOCKED and slot.locked_until and slot.locked_until < now_tz)
            )

            if not can_lock:
                logger.warning("Database check failed, slot not lockable", slot_id=str(slot_id), current_status=slot.status)
                await redis_client.delete(redis_key)
                return False

            # 3. Update slot lock parameters
            slot.status = SlotStatus.LOCKED
            slot.locked_until = now_tz + datetime.timedelta(seconds=ttl)
            slot.locked_by = locked_by

            await db.commit()
            logger.info("Successfully locked slot", slot_id=str(slot_id), locked_by=locked_by, until=str(slot.locked_until))
            return True

        except Exception as e:
            logger.error("Exception occurred during slot lock", error=str(e), slot_id=str(slot_id))
            # Cleanup Redis lock in case of database exception
            await redis_client.delete(redis_key)
            return False

    @classmethod
    async def release_slot(cls, db: AsyncSession, slot_id: uuid.UUID, locked_by: str) -> bool:
        """Release a slot lock if the session matches."""
        redis_key = f"lock:slot:{slot_id}"

        try:
            slot = await db.get(DoctorSlot, slot_id)
            if not slot:
                return False

            # If the database lock matches or is expired, we release it
            if slot.status == SlotStatus.LOCKED and slot.locked_by == locked_by:
                slot.status = SlotStatus.AVAILABLE
                slot.locked_until = None
                slot.locked_by = None
                await db.commit()

            # Always clean up Redis
            await redis_client.delete(redis_key)
            logger.info("Released slot lock", slot_id=str(slot_id), locked_by=locked_by)
            return True

        except Exception as e:
            logger.error("Failed to release slot lock", error=str(e), slot_id=str(slot_id))
            return False
