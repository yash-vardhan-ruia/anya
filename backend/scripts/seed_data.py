"""
CareVoice AI Hospital Platform - Database Seeding Script.

Seeds default admin user, hospital departments, active doctors, and recurring weekly schedules.
"""

import asyncio
import datetime
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, engine
from app.models.base import Base
from app.models.admin_user import AdminUser
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.schedule import DoctorSchedule
from app.core.constants import AdminRole
from app.core.security import hash_password

logger = structlog.get_logger(__name__)

# Sample Seeding Datasets
DEPARTMENTS_DATA = [
    {"name": "Cardiology", "description": "Expert heart care, electrophysiology, and coronary treatments.", "is_active": True},
    {"name": "Orthopedics", "description": "Bone, joint, spine surgeries, and sports medicine.", "is_active": True},
    {"name": "General Medicine", "description": "Primary healthcare, preventive diagnostics, and chronic wellness.", "is_active": True},
    {"name": "Pediatrics", "description": "Newborn, child healthcare, vaccinations, and growth diagnostics.", "is_active": True},
    {"name": "Dermatology", "description": "Skin, hair care, clinical treatments, and cosmetic diagnostics.", "is_active": True},
]

DOCTORS_DATA = [
    # Cardiology
    {
        "dept_name": "Cardiology",
        "full_name": "Dr. Ramesh Iyer",
        "specialization": "Interventional Cardiologist",
        "qualification": "MD (Medicine), DM (Cardiology), FACC",
        "experience_years": 16,
        "consultation_fee": 100000,  # INR 1000.00
        "phone": "+919988776655",
        "email": "ramesh.iyer@carevoice.ai",
        "schedules": [
            {"day_of_week": 0, "start_time": datetime.time(9, 0), "end_time": datetime.time(13, 0)},  # Mon morning
            {"day_of_week": 2, "start_time": datetime.time(9, 0), "end_time": datetime.time(13, 0)},  # Wed morning
            {"day_of_week": 4, "start_time": datetime.time(14, 0), "end_time": datetime.time(18, 0)}, # Fri afternoon
        ]
    },
    # Orthopedics
    {
        "dept_name": "Orthopedics",
        "full_name": "Dr. Sarah D'Souza",
        "specialization": "Joint Replacement Specialist",
        "qualification": "MS (Orthopedics), MCh (Ortho - UK)",
        "experience_years": 12,
        "consultation_fee": 85000,   # INR 850.00
        "phone": "+919988776654",
        "email": "sarah.dsouza@carevoice.ai",
        "schedules": [
            {"day_of_week": 1, "start_time": datetime.time(10, 0), "end_time": datetime.time(14, 0)}, # Tue morning
            {"day_of_week": 3, "start_time": datetime.time(10, 0), "end_time": datetime.time(14, 0)}, # Thu morning
        ]
    },
    # General Medicine
    {
        "dept_name": "General Medicine",
        "full_name": "Dr. Amit Sharma",
        "specialization": "General Physician",
        "qualification": "MBBS, MD (General Medicine)",
        "experience_years": 10,
        "consultation_fee": 50000,   # INR 500.00
        "phone": "+919988776653",
        "email": "amit.sharma@carevoice.ai",
        "schedules": [
            {"day_of_week": 0, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},  # Mon Full Day
            {"day_of_week": 1, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},  # Tue Full Day
            {"day_of_week": 2, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},  # Wed Full Day
            {"day_of_week": 3, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},  # Thu Full Day
            {"day_of_week": 4, "start_time": datetime.time(9, 0), "end_time": datetime.time(17, 0)},  # Fri Full Day
        ]
    },
    # Pediatrics
    {
        "dept_name": "Pediatrics",
        "full_name": "Dr. Ananya Rao",
        "specialization": "Consultant Pediatrician",
        "qualification": "MBBS, DCH, DNB (Pediatrics)",
        "experience_years": 8,
        "consultation_fee": 60000,   # INR 600.00
        "phone": "+919988776652",
        "email": "ananya.rao@carevoice.ai",
        "schedules": [
            {"day_of_week": 1, "start_time": datetime.time(9, 0), "end_time": datetime.time(12, 0)},  # Tue Morning
            {"day_of_week": 3, "start_time": datetime.time(14, 0), "end_time": datetime.time(17, 0)}, # Thu Afternoon
            {"day_of_week": 5, "start_time": datetime.time(9, 0), "end_time": datetime.time(13, 0)},  # Sat Morning
        ]
    }
]


async def seed() -> None:
    """Core async runner to perform database insertion."""
    # 0. Automatically create tables if they do not exist (perfect for clean Supabase runs)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize database tables", error=str(e))
        raise

    async with async_session_factory() as session:
        try:
            logger.info("Starting database seeding...")

            # 1. Seed default super admin if none exists
            admin_stmt = select(AdminUser).where(AdminUser.email == "admin@carevoice.ai")
            existing_admin = (await session.execute(admin_stmt)).scalar_one_or_none()
            if not existing_admin:
                super_admin = AdminUser(
                    email="admin@carevoice.ai",
                    hashed_password=hash_password("password123"),
                    full_name="Hospital Director",
                    role=AdminRole.SUPER_ADMIN,
                    is_active=True,
                )
                session.add(super_admin)
                logger.info("Seeded default Super Admin user (admin@carevoice.ai / password123)")
            else:
                logger.info("Super Admin user admin@carevoice.ai already exists, skipping...")

            # 2. Seed departments
            dept_cache = {}
            for dept_info in DEPARTMENTS_DATA:
                dept_stmt = select(Department).where(Department.name == dept_info["name"])
                existing_dept = (await session.execute(dept_stmt)).scalar_one_or_none()
                if not existing_dept:
                    dept = Department(
                        name=dept_info["name"],
                        description=dept_info["description"],
                        is_active=dept_info["is_active"],
                    )
                    session.add(dept)
                    await session.flush()
                    dept_cache[dept.name] = dept.id
                    logger.info("Seeded department", name=dept.name)
                else:
                    dept_cache[existing_dept.name] = existing_dept.id
                    logger.info("Department already exists", name=existing_dept.name)

            # 3. Seed doctors and recurring schedule templates
            for doc_info in DOCTORS_DATA:
                doc_stmt = select(Doctor).where(Doctor.email == doc_info["email"])
                existing_doc = (await session.execute(doc_stmt)).scalar_one_or_none()
                
                dept_id = dept_cache.get(doc_info["dept_name"])
                if not dept_id:
                    logger.warning("Department not found for doctor", dept_name=doc_info["dept_name"], doc=doc_info["full_name"])
                    continue

                if not existing_doc:
                    doc = Doctor(
                        department_id=dept_id,
                        full_name=doc_info["full_name"],
                        specialization=doc_info["specialization"],
                        qualification=doc_info["qualification"],
                        experience_years=doc_info["experience_years"],
                        consultation_fee=doc_info["consultation_fee"],
                        phone=doc_info["phone"],
                        email=doc_info["email"],
                        is_active=True
                    )
                    session.add(doc)
                    await session.flush()
                    logger.info("Seeded Doctor", name=doc.full_name)

                    # Create schedule templates for this new doctor
                    for sched in doc_info["schedules"]:
                        new_sched = DoctorSchedule(
                            doctor_id=doc.id,
                            day_of_week=sched["day_of_week"],
                            start_time=sched["start_time"],
                            end_time=sched["end_time"],
                            slot_duration_minutes=30,
                            is_active=True
                        )
                        session.add(new_sched)
                    logger.info("Seeded schedule templates for doctor", name=doc.full_name)
                else:
                    logger.info("Doctor already exists, skipping schedule seeding", email=doc_info["email"])

            await session.commit()
            logger.info("Database seeding successfully completed!")

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to seed database", error=str(e))
            raise


if __name__ == "__main__":
    asyncio.run(seed())
