import asyncio
from sqlalchemy import text
from app.database import async_session_factory

async def main():
    print("Updating doctor consultation fees in database...")
    async with async_session_factory() as session:
        try:
            await session.execute(text("UPDATE doctors SET consultation_fee = 100;"))
            await session.commit()
            print("Successfully updated every doctor's fee to 100 paise (1 INR)!")
        except Exception as e:
            await session.rollback()
            print(f"Error updating fees: {e}")

if __name__ == "__main__":
    asyncio.run(main())
