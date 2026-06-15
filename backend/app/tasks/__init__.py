"""
CareVoice AI Hospital Platform - Background Tasks Package.

Exposes Celery app instance and registered tasks.
"""

from app.tasks.celery_app import celery_app
from app.tasks.notification_tasks import send_appointment_notifications, send_payment_link_email_task

__all__ = [
    "celery_app",
    "send_appointment_notifications",
    "send_payment_link_email_task",
]
