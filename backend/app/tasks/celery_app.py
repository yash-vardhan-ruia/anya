"""
CareVoice AI Hospital Platform - Celery Core Configuration.

Configures Celery distributed task queue to handle asynchronous workflows (e.g. notifications).
"""

from celery import Celery
from app.config import settings

# Initialize Celery using Redis as both broker and backend
celery_app = Celery(
    "carevoice_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.notification_tasks"],
)

# Standard performance/reliability configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes maximum runtime
)
