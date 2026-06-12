"""
Twilio webhook handlers - incoming voice calls and status callbacks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.call_session import CallSession
from app.core.constants import CallStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/twilio/voice",
    status_code=status.HTTP_200_OK,
    summary="Handle incoming Twilio voice call",
)
async def handle_twilio_voice(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form("ringing"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Handle an incoming Twilio voice call.

    Creates a new CallSession in the database and returns TwiML that connects
    the call to a WebSocket media stream for real-time AI voice processing.
    """
    logger.info(
        "Incoming Twilio voice call: CallSid=%s, From=%s, To=%s",
        CallSid,
        From,
        To,
    )

    call_session = CallSession(
        twilio_call_sid=CallSid,
        from_number=From,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(call_session)
    await db.commit()
    await db.refresh(call_session)

    # ws protocol should match the scheme (wss for https, ws for http)
    base_url = settings.BASE_URL.rstrip("/")
    clean_host = base_url.replace("https://", "").replace("http://", "")
    protocol = "wss" if base_url.startswith("https") else "ws"
    ws_url = f"{protocol}://{clean_host}/ws/voice/{CallSid}"

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Connect>"
        f'<Stream url="{ws_url}"/>'
        "</Connect>"
        "</Response>"
    )

    return Response(content=twiml, media_type="application/xml")


@router.post(
    "/twilio/status",
    status_code=status.HTTP_200_OK,
    summary="Handle Twilio status callback",
)
async def handle_twilio_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Twilio call status callback.

    Updates the CallSession record with the latest status and timestamps
    when the call completes or changes state.
    """
    logger.info(
        "Twilio status callback: CallSid=%s, Status=%s, Duration=%s",
        CallSid,
        CallStatus,
        CallDuration,
    )

    from sqlalchemy import select

    result = await db.execute(
        select(CallSession).where(CallSession.twilio_call_sid == CallSid)
    )
    call_session = result.scalar_one_or_none()

    if call_session is None:
        logger.warning("CallSession not found for CallSid: %s", CallSid)
        return {"status": "not_found"}

    call_session.status = CallStatus

    # Map status to ended_at or started_at if needed
    if CallStatus == "in-progress" and call_session.started_at is None:
        call_session.started_at = datetime.now(timezone.utc)

    if CallStatus in ("completed", "failed", "busy", "no-answer", "canceled"):
        if call_session.started_at is None:
            # Safe fallback if connect webhook wasn't logged correctly
            call_session.started_at = call_session.created_at
        call_session.ended_at = datetime.now(timezone.utc)

    await db.commit()

    return {"status": "ok"}
