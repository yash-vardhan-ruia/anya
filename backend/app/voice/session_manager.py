"""
CareVoice AI Hospital Platform - Voice Session Manager.

Redis-backed state and memory manager to track patient conversation state machine
and variables during a live Twilio voice call session.
"""

import datetime
import json
import structlog
import redis.asyncio as aioredis
from app.config import settings
from app.core.constants import ConversationState

logger = structlog.get_logger(__name__)

# Initialize async Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class VoiceSessionManager:
    """Manages conversational session state machine variables in Redis."""

    @staticmethod
    def _get_key(call_sid: str) -> str:
        return f"voice:session:{call_sid}"

    @classmethod
    async def get_session(cls, call_sid: str) -> dict | None:
        """Fetch the current voice booking session state from Redis."""
        key = cls._get_key(call_sid)
        try:
            data = await redis_client.get(key)
            if not data:
                return None
            return json.loads(data)
        except Exception as e:
            logger.error("Failed to read voice session from Redis", error=str(e), call_sid=call_sid)
            return None

    @classmethod
    async def save_session(cls, call_sid: str, session_data: dict, ex: int = 1800) -> None:
        """Save/overwrite the voice booking session state in Redis with a 30-min TTL."""
        key = cls._get_key(call_sid)
        try:
            await redis_client.set(key, json.dumps(session_data), ex=ex)
        except Exception as e:
            logger.error("Failed to save voice session to Redis", error=str(e), call_sid=call_sid)

    @classmethod
    async def update_session(cls, call_sid: str, updates: dict) -> dict:
        """Update specific fields in the voice session state."""
        session = await cls.get_session(call_sid)
        if not session:
            # Initialize a blank premium state structure
            session = {
                "call_sid": call_sid,
                "current_state": ConversationState.GREETING.value,
                "patient_id": None,
                "patient_name": None,
                "phone": None,
                "symptoms": None,
                "department_id": None,
                "department_name": None,
                "doctor_id": None,
                "doctor_name": None,
                "slot_id": None,
                "slot_time_str": None,
                "slot_date_str": None,
                "invoice_id": None,
                "is_emergency": False,
                "created_at": str(datetime.datetime.now()),
            }

        session.update(updates)
        await cls.save_session(call_sid, session)
        return session

    @classmethod
    async def clear_session(cls, call_sid: str) -> None:
        """Delete the voice session from Redis."""
        key = cls._get_key(call_sid)
        try:
            await redis_client.delete(key)
            logger.info("Cleared voice session from Redis", call_sid=call_sid)
        except Exception as e:
            logger.error("Failed to clear voice session from Redis", error=str(e), call_sid=call_sid)



