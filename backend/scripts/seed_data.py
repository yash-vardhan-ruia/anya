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

            await session.commit()
            logger.info("Database seeding successfully completed!")

        except Exception as e:
            await session.rollback()
            logger.exception("Failed to seed database", error=str(e))
            raise


if __name__ == "__main__":
    asyncio.run(seed())
