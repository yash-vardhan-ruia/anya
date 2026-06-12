"""
CareVoice AI Hospital Platform - Voice Call Handler.

Exposes traditional Twilio TwiML voice endpoints to handle incoming calls and connect
them to our low-latency WebSocket bridging server.
"""

import logging
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import Response

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/incoming",
    status_code=status.HTTP_200_OK,
    summary="TwiML response to connect incoming calls to WebSocket bridge",
)
async def incoming_twilio_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
) -> Response:
    """Entry point for Twilio phone numbers.

    Returns the XML TwiML instructions directing Twilio to open a WebSocket
    Stream to our real-time voice bridging agent.
    """
    logger.info("Incoming Twilio call request received", call_sid=CallSid, caller=From)

    base_url = settings.BASE_URL.rstrip("/")
    clean_host = base_url.replace("https://", "").replace("http://", "")
    protocol = "wss" if base_url.startswith("https") else "ws"
    ws_url = f"{protocol}://{clean_host}/ws/voice/{CallSid}?from_phone={From}&to_phone={To}"

    # Connect Twilio Media Stream to WebSocket bridge
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Say voice='Polly.Amy' language='en-GB'>Connecting you to Anya, your CareVoice medical receptionist. Please wait.</Say>"
        "<Connect>"
        f'<Stream url="{ws_url}"/>'
        "</Connect>"
        "</Response>"
    )

    return Response(content=twiml, media_type="application/xml")
