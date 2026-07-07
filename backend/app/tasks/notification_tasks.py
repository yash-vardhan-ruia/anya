"""
CareVoice AI Hospital Platform - Celery Notification Tasks.

Defines asynchronous background tasks to send email/SMS confirmation and updates
without blocking main API responses.
"""

import asyncio
import uuid
import structlog
from app.tasks.celery_app import celery_app
from app.database import async_session_factory
from app.services.notification_service import NotificationService

logger = structlog.get_logger(__name__)


async def _async_send_notifications(appointment_id_str: str, event_type: str) -> None:
    """Async wrapper that performs database fetching and executes notification clients."""
    appointment_id = uuid.UUID(appointment_id_str)
    
    async with async_session_factory() as db:
        try:
            if event_type == "created":
                logger.info("Executing async notification for appointment created", id=appointment_id_str)
                await NotificationService.send_appointment_created(db, appointment_id)
            elif event_type == "confirmed":
                logger.info("Executing async notification for appointment confirmed", id=appointment_id_str)
                await NotificationService.send_appointment_confirmed(db, appointment_id)
            elif event_type == "cancelled":
                logger.info("Executing async notification for appointment cancelled", id=appointment_id_str)
                await NotificationService.send_appointment_cancelled(db, appointment_id)
            else:
                logger.warning("Unrecognized notification event type in Celery worker", evt_type=event_type)
        except Exception as e:
            logger.exception("Failed to send notification via Celery worker", error=str(e), appointment_id=appointment_id_str)
            raise


@celery_app.task(name="app.tasks.notification_tasks.send_appointment_notifications", queue="notifications")
def send_appointment_notifications(appointment_id_str: str, event_type: str) -> str:
    """Celery entry point to asynchronously handle SMS/Email dispatch."""
    logger.info("Celery task received send_appointment_notifications", id=appointment_id_str, evt_type=event_type)
    
    # Run the async database operations within the sync Celery thread
    asyncio.run(_async_send_notifications(appointment_id_str, event_type))
    
    return f"Notifications dispatched successfully for {appointment_id_str} ({event_type})"


@celery_app.task(name="app.tasks.notification_tasks.send_payment_link_email_task", queue="notifications")
def send_payment_link_email_task(
    email: str, patient_name: str, doctor_name: str, amount_inr: float, payment_url: str
) -> str:
    """Celery task to send payment link email asynchronously."""
    logger.info("Celery task received send_payment_link_email_task", email=email)
    
    # Run the async email dispatch within the sync Celery thread
    asyncio.run(
        NotificationService.send_payment_link_email(
            email=email,
            patient_name=patient_name,
            doctor_name=doctor_name,
            amount=amount_inr,
            payment_url=payment_url,
        )
    )
    return f"Payment link email dispatched successfully to {email}"

