"""
CareVoice AI Hospital Platform - Integrations Package.

Exposes external client wrappers for Razorpay and SMTP Email.
"""

from app.integrations.razorpay_client import razorpay_client
from app.integrations.email_client import email_client

__all__ = [
    "razorpay_client",
    "email_client",
]
