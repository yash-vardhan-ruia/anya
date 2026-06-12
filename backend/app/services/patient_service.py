"""
CareVoice AI Hospital Platform - Patient Service.

Handles business logic for patient CRUD operations, including automated MRN generation
and lookup/creation by phone number during voice calls.
"""

import random
import uuid
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

logger = structlog.get_logger(__name__)


class PatientService:
    """Business logic for Patient registration and management."""

    @staticmethod
    def _generate_mrn() -> str:
        """Generate a unique Medical Record Number (MRN)."""
        # Format: MRN-YYYYMMDD-XXXX where X is a random digit
        import datetime
        today_str = datetime.date.today().strftime("%Y%m%d")
        rand_digits = "".join(str(random.randint(0, 9)) for _ in range(4))
        return f"MRN-{today_str}-{rand_digits}"

    @classmethod
    async def get_patient(cls, db: AsyncSession, patient_id: uuid.UUID) -> Patient | None:
        """Retrieve a patient by their primary key UUID."""
        return await db.get(Patient, patient_id)

    @classmethod
    async def get_patient_by_phone(cls, db: AsyncSession, phone: str) -> Patient | None:
        """Retrieve a patient by their unique phone number."""
        stmt = select(Patient).where(Patient.phone == phone)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_or_create_patient_by_phone(
        cls,
        db: AsyncSession,
        phone: str,
        full_name: str,
    ) -> Patient:
        """Find an existing patient by phone or register a new one.

        Used by the voice assistant flow to quickly identify patients.
        """
        patient = await cls.get_patient_by_phone(db, phone)
        if patient:
            logger.info("Patient identified by phone", phone=phone, patient_id=str(patient.id))
            return patient

        # If not found, create new patient
        mrn = cls._generate_mrn()
        # Verify MRN uniqueness in case of collison (highly unlikely, but safe)
        while True:
            stmt = select(Patient).where(Patient.medical_record_number == mrn)
            dup = (await db.execute(stmt)).scalar_one_or_none()
            if not dup:
                break
            mrn = cls._generate_mrn()

        new_patient = Patient(
            phone=phone,
            full_name=full_name,
            medical_record_number=mrn,
        )
        db.add(new_patient)
        await db.flush()  # Populates new_patient.id
        logger.info("Registered new patient during call session", phone=phone, mrn=mrn, patient_id=str(new_patient.id))
        return new_patient

    @classmethod
    async def create_patient(cls, db: AsyncSession, schema: PatientCreate) -> Patient:
        """Create a new patient from the dashboard."""
        mrn = cls._generate_mrn()
        new_patient = Patient(
            phone=schema.phone,
            full_name=schema.full_name,
            email=schema.email,
            date_of_birth=schema.date_of_birth,
            gender=schema.gender,
            address=schema.address,
            medical_record_number=mrn,
        )
        db.add(new_patient)
        await db.commit()
        await db.refresh(new_patient)
        logger.info("Created new patient record from admin dashboard", mrn=mrn, patient_id=str(new_patient.id))
        return new_patient

    @classmethod
    async def update_patient(cls, db: AsyncSession, patient_id: uuid.UUID, schema: PatientUpdate) -> Patient | None:
        """Update an existing patient's details."""
        patient = await cls.get_patient(db, patient_id)
        if not patient:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(patient, key, value)

        await db.commit()
        await db.refresh(patient)
        logger.info("Updated patient record", patient_id=str(patient_id))
        return patient

    @classmethod
    async def list_patients(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search_query: str | None = None,
    ) -> tuple[int, list[Patient]]:
        """List patient records with optional search filter."""
        stmt = select(Patient)
        if search_query:
            stmt = stmt.where(
                Patient.full_name.ilike(f"%{search_query}%")
                | Patient.phone.ilike(f"%{search_query}%")
                | Patient.medical_record_number.ilike(f"%{search_query}%")
            )

        # Count query
        count_stmt = select(select(Patient).where(False).exists())  # placeholder helper
        # A simpler way to count is using func.count:
        from sqlalchemy import func
        if search_query:
            count_stmt = select(func.count(Patient.id)).where(
                Patient.full_name.ilike(f"%{search_query}%")
                | Patient.phone.ilike(f"%{search_query}%")
                | Patient.medical_record_number.ilike(f"%{search_query}%")
            )
        else:
            count_stmt = select(func.count(Patient.id))
            
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset(skip).limit(limit).order_by(Patient.created_at.desc())
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return total, items
