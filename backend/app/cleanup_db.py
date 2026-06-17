import asyncio
from sqlalchemy import text
from app.database import async_session_factory

async def main():
    print("Connecting to database for schema cleanup...")
    async with async_session_factory() as session:
        try:
            # 1. Drop audit_logs and emergency_incidents tables if they exist
            print("Dropping unused tables: audit_logs, emergency_incidents...")
            await session.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE;"))
            await session.execute(text("DROP TABLE IF EXISTS emergency_incidents CASCADE;"))
            
            # 2. Update doctor consultation fees to 100 paise (1 INR)
            print("Updating doctor consultation fees to 100 paise (1 INR)...")
            await session.execute(text("UPDATE doctors SET consultation_fee = 100;"))
            
            await session.commit()
            print("Database schema cleanup and doctor fees update completed successfully!")
        except Exception as e:
            await session.rollback()
            print(f"Error during database cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(main())
