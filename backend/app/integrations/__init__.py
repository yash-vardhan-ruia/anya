"""
CareVoice AI Hospital Platform - Integrations Package.

Exposes external client wrappers for Twilio, Razorpay, and SMTP Email.
"""

from app.integrations.razorpay_client import razorpay_client
from app.integrations.twilio_client import twilio_client
from app.integrations.email_client import email_client

__all__ = [
    "razorpay_client",
    "twilio_client",
    "email_client",
]
