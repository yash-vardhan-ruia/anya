"""
CareVoice AI Hospital Platform - Twilio Integration Client.

Wrapper around the Twilio SDK to support SMS notifications and outbound call initiation.
"""

import structlog
from twilio.rest import Client
from app.config import settings

logger = structlog.get_logger(__name__)


class TwilioClient:
    """Client wrapper for Twilio messaging and voice operations."""

    def __init__(self) -> None:
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self._client = None

        if self.account_sid and self.auth_token:
            self._client = Client(self.account_sid, self.auth_token)
        else:
            logger.warning("Twilio credentials not configured. SMS and Calls will be simulated.")

    def send_sms(self, to_phone: str, body: str) -> str:
        """Send an SMS notification using Twilio.

        Args:
            to_phone: Recipient phone number (e.g. +91XXXXXXXXXX)
            body: The text message content

        Returns:
            str: Twilio Message SID, or simulated SID if credentials missing.
        """
        if not self._client:
            logger.info("Twilio Client simulated SMS", to=to_phone, body=body)
            import uuid
            return f"SMsim_{uuid.uuid4().hex[:20]}"

        try:
            message = self._client.messages.create(
                body=body,
                from_=self.from_phone,
                to=to_phone
            )
            logger.info("SMS sent successfully via Twilio", message_sid=message.sid, to=to_phone)
            return message.sid
        except Exception as e:
            logger.error("Failed to send SMS via Twilio", error=str(e), to=to_phone)
            raise RuntimeError(f"Twilio SMS sending failed: {e}")

    def initiate_call(self, to_phone: str, callback_url: str) -> str:
        """Initiate an outbound call that connects to the CareVoice Voice flow.

        Args:
            to_phone: Patient's phone number
            callback_url: The webhook endpoint that returns TwiML instructions for the call

        Returns:
            str: Twilio Call SID, or simulated SID if credentials missing.
        """
        if not self._client:
            logger.info("Twilio Client simulated outbound call", to=to_phone, callback_url=callback_url)
            import uuid
            return f"CAsim_{uuid.uuid4().hex[:20]}"

        try:
            call = self._client.calls.create(
                url=callback_url,
                to=to_phone,
                from_=self.from_phone,
                record=False,
            )
            logger.info("Outbound call initiated successfully via Twilio", call_sid=call.sid, to=to_phone)
            return call.sid
        except Exception as e:
            logger.error("Failed to initiate call via Twilio", error=str(e), to=to_phone)
            raise RuntimeError(f"Twilio call initiation failed: {e}")


# Singleton client instance
twilio_client = TwilioClient()
