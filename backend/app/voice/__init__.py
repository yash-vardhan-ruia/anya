"""
CareVoice AI Hospital Platform - Voice Package.

Exposes routers for Twilio TwiML webhooks and WebSocket audio streams.
"""

from app.voice.handler import router as voice_router
from app.voice.bridge import router as ws_router

__all__ = [
    "voice_router",
    "ws_router",
]
