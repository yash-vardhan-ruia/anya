"""
CareVoice AI Hospital Platform - Doctor & Department Service.

Handles CRUD operations for doctors, department management, and doctor-department relations.
"""

import uuid
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.doctor import Doctor
from app.models.department import Department
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorScheduleCreate
from app.schemas.department import DepartmentCreate, DepartmentUpdate

logger = structlog.get_logger(__name__)


class DoctorService:
    """Business logic for Doctors and Hospital Departments."""

    # --- Department Methods ---

    @classmethod
    async def get_department(cls, db: AsyncSession, department_id: uuid.UUID) -> Department | None:
        """Retrieve a department by ID."""
        return await db.get(Department, department_id)

    @classmethod
    async def get_department_by_name(cls, db: AsyncSession, name: str) -> Department | None:
        """Retrieve a department by its unique name (case-insensitive)."""
        stmt = select(Department).where(func.lower(Department.name) == func.lower(name))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create_department(cls, db: AsyncSession, schema: DepartmentCreate) -> Department:
        """Create a new hospital department."""
        new_dept = Department(
            name=schema.name,
            description=schema.description,
            is_active=schema.is_active,
        )
        db.add(new_dept)
        await db.commit()
        await db.refresh(new_dept)
        logger.info("Created department", name=new_dept.name, id=str(new_dept.id))
        return new_dept

    @classmethod
    async def update_department(
        cls, db: AsyncSession, department_id: uuid.UUID, schema: DepartmentUpdate
    ) -> Department | None:
        """Update an existing department."""
        dept = await cls.get_department(db, department_id)
        if not dept:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dept, key, value)

        await db.commit()
        await db.refresh(dept)
        logger.info("Updated department", id=str(department_id))
        return dept

    @classmethod
    async def list_departments(
        cls, db: AsyncSession, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> tuple[int, list[Department]]:
        """List all departments."""
        stmt = select(Department)
        if active_only:
            stmt = stmt.where(Department.is_active == True)

        count_stmt = select(func.count(Department.id))
        if active_only:
            count_stmt = count_stmt.where(Department.is_active == True)
        
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Department.name.asc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items

    # --- Doctor Methods ---

    @classmethod
    async def get_doctor(cls, db: AsyncSession, doctor_id: uuid.UUID) -> Doctor | None:
        """Retrieve a doctor by ID."""
        return await db.get(Doctor, doctor_id)

    @classmethod
    async def create_doctor(cls, db: AsyncSession, schema: DoctorCreate) -> Doctor:
        """Register a new doctor in a department."""
        new_doctor = Doctor(
            department_id=schema.department_id,
            full_name=schema.full_name,
            specialization=schema.specialization,
            qualification=schema.qualification,
            experience_years=schema.experience_years,
            consultation_fee=schema.consultation_fee,
            phone=schema.phone,
            email=schema.email,
            is_active=schema.is_active,
        )
        db.add(new_doctor)
        await db.commit()
        await db.refresh(new_doctor)
        logger.info("Registered new doctor", doctor_name=new_doctor.full_name, id=str(new_doctor.id))
        return new_doctor

    @classmethod
    async def update_doctor(
        cls, db: AsyncSession, doctor_id: uuid.UUID, schema: DoctorUpdate
    ) -> Doctor | None:
        """Update doctor professional details or active status."""
        doctor = await cls.get_doctor(db, doctor_id)
        if not doctor:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doctor, key, value)

        await db.commit()
        await db.refresh(doctor)
        logger.info("Updated doctor details", id=str(doctor_id))
        return doctor

    @classmethod
    async def list_doctors(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        department_id: uuid.UUID | None = None,
        active_only: bool = False,
    ) -> tuple[int, list[Doctor]]:
        """List doctors, optionally filtering by department or active status."""
        stmt = select(Doctor)
        if department_id:
            stmt = stmt.where(Doctor.department_id == department_id)
        if active_only:
            stmt = stmt.where(Doctor.is_active == True)

        count_stmt = select(func.count(Doctor.id))
        if department_id:
            count_stmt = count_stmt.where(Doctor.department_id == department_id)
        if active_only:
            count_stmt = count_stmt.where(Doctor.is_active == True)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Doctor.full_name.asc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items

    # --- Schedule Methods ---

    @classmethod
    async def create_schedule(
        cls, db: AsyncSession, doctor_id: uuid.UUID, schema: DoctorScheduleCreate
    ) -> "DoctorSchedule":
        """Create a recurring schedule for a doctor."""
        from app.models.schedule import DoctorSchedule
        new_schedule = DoctorSchedule(
            doctor_id=doctor_id,
            day_of_week=schema.day_of_week,
            start_time=schema.start_time,
            end_time=schema.end_time,
            slot_duration_minutes=schema.slot_duration_minutes,
            is_active=schema.is_active,
        )
        db.add(new_schedule)
        await db.commit()
        await db.refresh(new_schedule)
        logger.info("Created doctor schedule", doctor_id=str(doctor_id), schedule_id=str(new_schedule.id))
        return new_schedule

    @classmethod
    async def list_schedules(
        cls, db: AsyncSession, doctor_id: uuid.UUID
    ) -> list["DoctorSchedule"]:
        """List all recurring schedules for a doctor."""
        from app.models.schedule import DoctorSchedule
        stmt = select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id).order_by(DoctorSchedule.day_of_week.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
