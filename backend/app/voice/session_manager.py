"""
CareVoice AI Hospital Platform - Voice Session Manager.

Redis-backed session store for voice conversation state.
Manages the full EHR variable set that powers the frontend panel and FSM.
"""

import json
import datetime
import structlog
from typing import Any

from app.core.constants import ConversationState

logger = structlog.get_logger(__name__)

SESSION_TTL = 1800  # 30 minutes


class VoiceSessionManager:
    """Manages voice session state backed by Redis."""

    _redis = None

    @classmethod
    async def _get_redis(cls):
        if cls._redis is None:
            import redis.asyncio as aioredis
            from app.config import settings
            cls._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return cls._redis

    @classmethod
    def _key(cls, session_id: str) -> str:
        return f"voice:session:{session_id}"

    @classmethod
    def _default_session(cls, session_id: str) -> dict:
        """Return a fresh default session for a new call."""
        return {
            "session_id": session_id,
            "current_state": ConversationState.GREETING,

            # --- Patient Identity ---
            "patient_type": None,       # "new" | "returning"
            "patient_id": None,         # UUID str after creation/lookup
            "patient_name": None,       # Full name (voice input)
            "age": None,                # Age (voice input) — key "age" matches frontend
            "gender": None,             # Gender (voice input)
            "email": None,              # Email (browser text input) — key "email" matches frontend
            "visit_type": None,         # "new" | "returning" — shown in EHR panel

            # --- Clinical ---
            "symptoms": None,           # Free-text symptoms from voice

            # --- Department ---
            "department_id": None,
            "department_name": None,

            # --- Doctor ---
            "doctor_id": None,
            "doctor_name": None,

            # --- Slot ---
            "slot_id": None,
            "slot_date_str": None,      # Human-readable: "Mon, 23 Jun 2026" — matches frontend
            "slot_time_str": None,      # Human-readable: "10:30 AM - 11:00 AM" — matches frontend

            # --- Booking ---
            "appointment_id": None,
            "amount_inr": None,         # Float, consultation fee + GST

            # --- Payment ---
            "payment_link_url": None,   # Razorpay short URL — shown in frontend EHR panel
            "payment_sent": False,

            # --- Emergency ---
            "is_emergency": False,

            # --- Internal (not shown in EHR panel) ---
            "available_doctors": [],    # List of doctor dicts from last find_doctors_by_department call
            "available_slots": [],      # List of slot dicts from last get_available_slots call
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    @classmethod
    async def get_session(cls, session_id: str) -> dict:
        """Retrieve session from Redis or create a fresh one."""
        redis = await cls._get_redis()
        key = cls._key(session_id)
        raw = await redis.get(key)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Corrupt session data — resetting", session_id=session_id)

        session = cls._default_session(session_id)
        await cls.save_session(session_id, session)
        return session

    @classmethod
    async def save_session(cls, session_id: str, data: dict) -> None:
        """Persist the full session to Redis with TTL refresh."""
        redis = await cls._get_redis()
        await redis.set(cls._key(session_id), json.dumps(data, default=str), ex=SESSION_TTL)

    @classmethod
    async def update_session(cls, session_id: str, updates: dict) -> dict:
        """Apply partial updates and return the full updated session."""
        session = await cls.get_session(session_id)
        session.update(updates)
        await cls.save_session(session_id, session)
        logger.debug("Session updated", session_id=session_id, keys=list(updates.keys()))
        return session

    @classmethod
    async def clear_session(cls, session_id: str) -> None:
        """Delete session from Redis (call end cleanup)."""
        redis = await cls._get_redis()
        await redis.delete(cls._key(session_id))
        logger.info("Session cleared", session_id=session_id)
