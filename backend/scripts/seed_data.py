"""
CareVoice AI Hospital Platform - Database Seeding Script.

Seeds default admin user, hospital departments, active doctors, and recurring weekly schedules.
"""

import asyncio
import datetime
import structlog
from sqlalchemy import select, text
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

            # Ensure status column exists and types are correct on invoices/payments tables
            try:
                await session.execute(text("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL"))
                await session.execute(text("ALTER TABLE invoices DROP COLUMN IF EXISTS payment_method"))
                await session.execute(text("ALTER TABLE invoices ALTER COLUMN subtotal TYPE DOUBLE PRECISION"))
                await session.execute(text("ALTER TABLE invoices ALTER COLUMN gst_amount TYPE DOUBLE PRECISION"))
                await session.execute(text("ALTER TABLE invoices ALTER COLUMN total_amount TYPE DOUBLE PRECISION"))
                await session.execute(text("ALTER TABLE payments ALTER COLUMN amount TYPE DOUBLE PRECISION"))
                await session.commit()
                logger.info("Ensured correct database schema for invoices and payments tables.")
            except Exception as e:
                await session.rollback()
                logger.warning("Could not automatically alter tables schema", error=str(e))

            # Migrate existing user accounts to 'admin' or preserve 'super_admin'
            await session.execute(text("UPDATE admin_users SET role = 'admin' WHERE role NOT IN ('admin', 'super_admin')"))
            await session.commit()
            logger.info("Migrated existing admin user roles to 'admin'")

            # 1. Seed default admin if none exists
            admin_stmt = select(AdminUser).where(AdminUser.email == "admin@carevoice.ai")
            existing_admin = (await session.execute(admin_stmt)).scalar_one_or_none()
            if not existing_admin:
                default_admin = AdminUser(
                    email="admin@carevoice.ai",
                    hashed_password=hash_password("password123"),
                    full_name="Hospital Director",
                    role=AdminRole.SUPER_ADMIN,
                    is_active=True,
                )
                session.add(default_admin)
                logger.info("Seeded default Admin user (admin@carevoice.ai / password123) with SUPER_ADMIN role")
            else:
                existing_admin.role = AdminRole.SUPER_ADMIN
                logger.info("Admin user admin@carevoice.ai updated/ensured to SUPER_ADMIN role")

            # 2. Seed departments
            departments_to_seed = [
                "Cardiology", "Dermatology", "ENT", "Gastroenterology", 
                "General Medicine", "Neurology", "Oncology", "Ophthalmology", 
                "Orthopedics", "Pediatrics", "Psychiatry", "Pulmonology", 
                "Radiology", "Urology"
            ]
            
            department_ids = {}
            for dept_name in departments_to_seed:
                dept_stmt = select(Department).where(Department.name == dept_name)
                existing_dept = (await session.execute(dept_stmt)).scalar_one_or_none()
                if not existing_dept:
                    new_dept = Department(
                        name=dept_name,
                        description=f"Operational hospital department for {dept_name}.",
                        is_active=False  # initially inactive, will update below based on doctors
                    )
                    session.add(new_dept)
                    await session.flush()
                    department_ids[dept_name] = new_dept.id
                    logger.info("Seeded department", name=dept_name)
                else:
                    department_ids[dept_name] = existing_dept.id
            await session.commit()

            # 3. Seed doctors
            import uuid
            doctors_to_seed = [
                {
                    "full_name": "Dr. Ananya Rao",
                    "email": "ananya.rao@carevoice.ai",
                    "phone": "+919876543210",
                    "specialization": "Pediatrician",
                    "qualification": "MD - Pediatrics, MBBS",
                    "experience_years": 12,
                    "consultation_fee": 1.0,
                    "department_name": "Pediatrics",
                    "days": [0, 1, 2, 3, 4], # Mon-Fri
                    "start": datetime.time(9, 0),
                    "end": datetime.time(12, 0)
                },
                {
                    "full_name": "Dr. Arvind Sharma",
                    "email": "arvind.sharma@carevoice.ai",
                    "phone": "+919876543211",
                    "specialization": "Cardiologist",
                    "qualification": "DM - Cardiology, MD, MBBS",
                    "experience_years": 15,
                    "consultation_fee": 1.0,
                    "department_name": "Cardiology",
                    "days": [0, 2, 4], # Mon, Wed, Fri
                    "start": datetime.time(10, 0),
                    "end": datetime.time(14, 0)
                },
                {
                    "full_name": "Dr. Priya Patel",
                    "email": "priya.patel@carevoice.ai",
                    "phone": "+919876543212",
                    "specialization": "General Physician",
                    "qualification": "MD - Internal Medicine, MBBS",
                    "experience_years": 10,
                    "consultation_fee": 1.0,
                    "department_name": "General Medicine",
                    "days": [0, 1, 2, 3, 4, 5], # Mon-Sat
                    "start": datetime.time(9, 0),
                    "end": datetime.time(13, 0)
                },
                {
                    "full_name": "Dr. Rohan Mehta",
                    "email": "rohan.mehta@carevoice.ai",
                    "phone": "+919876543213",
                    "specialization": "Orthopedic Surgeon",
                    "qualification": "MS - Orthopedics, MBBS",
                    "experience_years": 8,
                    "consultation_fee": 1.0,
                    "department_name": "Orthopedics",
                    "days": [1, 3, 5], # Tue, Thu, Sat
                    "start": datetime.time(11, 0),
                    "end": datetime.time(15, 0)
                },
                {
                    "full_name": "Dr. Sarah D'Souza",
                    "email": "sarah.dsouza@carevoice.ai",
                    "phone": "+919876543214",
                    "specialization": "Dermatologist",
                    "qualification": "DDVL, MD - Dermatology, MBBS",
                    "experience_years": 7,
                    "consultation_fee": 1.0,
                    "department_name": "Dermatology",
                    "days": [0, 2, 5], # Mon, Wed, Sat
                    "start": datetime.time(14, 0),
                    "end": datetime.time(18, 0)
                },
                {
                    "full_name": "Dr. Rajesh Iyer",
                    "email": "rajesh.iyer@carevoice.ai",
                    "phone": "+919876543215",
                    "specialization": "Neurologist",
                    "qualification": "DM - Neurology, MD, MBBS",
                    "experience_years": 18,
                    "consultation_fee": 1.0,
                    "department_name": "Neurology",
                    "days": [1, 4], # Tue, Fri
                    "start": datetime.time(10, 0),
                    "end": datetime.time(13, 0)
                }
            ]
            
            for doc_data in doctors_to_seed:
                doc_stmt = select(Doctor).where(Doctor.email == doc_data["email"])
                existing_doc = (await session.execute(doc_stmt)).scalar_one_or_none()
                dept_id = department_ids[doc_data["department_name"]]
                
                if not existing_doc:
                    doc = Doctor(
                        department_id=dept_id,
                        full_name=doc_data["full_name"],
                        specialization=doc_data["specialization"],
                        qualification=doc_data["qualification"],
                        experience_years=doc_data["experience_years"],
                        consultation_fee=doc_data["consultation_fee"],
                        phone=doc_data["phone"],
                        email=doc_data["email"],
                        is_active=True
                    )
                    session.add(doc)
                    await session.flush()
                    doc_id = doc.id
                    logger.info("Seeded doctor", name=doc_data["full_name"])
                else:
                    existing_doc.department_id = dept_id
                    existing_doc.full_name = doc_data["full_name"]
                    existing_doc.specialization = doc_data["specialization"]
                    existing_doc.qualification = doc_data["qualification"]
                    existing_doc.experience_years = doc_data["experience_years"]
                    existing_doc.consultation_fee = doc_data["consultation_fee"]
                    existing_doc.phone = doc_data["phone"]
                    existing_doc.is_active = True
                    doc_id = existing_doc.id
                    logger.info("Ensured doctor", name=doc_data["full_name"])
                
                # Seed schedules for the doctor
                for day in doc_data["days"]:
                    sched_stmt = select(DoctorSchedule).where(
                        DoctorSchedule.doctor_id == doc_id,
                        DoctorSchedule.day_of_week == day
                    )
                    existing_sched = (await session.execute(sched_stmt)).scalar_one_or_none()
                    if not existing_sched:
                        sched = DoctorSchedule(
                            doctor_id=doc_id,
                            day_of_week=day,
                            start_time=doc_data["start"],
                            end_time=doc_data["end"],
                            slot_duration_minutes=30,
                            is_active=True
                        )
                        session.add(sched)
                    else:
                        existing_sched.start_time = doc_data["start"]
                        existing_sched.end_time = doc_data["end"]
                        existing_sched.slot_duration_minutes = 30
                        existing_sched.is_active = True
            await session.commit()

            # 4. Dynamically calculate and update is_active status of all departments
            from sqlalchemy import func
            for dept_name in departments_to_seed:
                dept_stmt = select(Department).where(Department.name == dept_name)
                dept = (await session.execute(dept_stmt)).scalar_one()
                
                # Count active doctors in this department
                count_stmt = select(func.count(Doctor.id)).where(
                    Doctor.department_id == dept.id,
                    Doctor.is_active == True
                )
                count_res = await session.execute(count_stmt)
                active_count = count_res.scalar_one()
                
                dept.is_active = (active_count > 0)
                logger.info("Updated department operational status", name=dept_name, active_doctors=active_count, is_active=dept.is_active)
            
            await session.commit()
            logger.info("Database seeding successfully completed!")

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to seed database", error=str(e))
            raise


if __name__ == "__main__":
    asyncio.run(seed())
