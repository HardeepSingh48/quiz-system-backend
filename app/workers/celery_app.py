"""Celery application configuration"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "quiz_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.notification_worker",
        "app.workers.leaderboard_worker",
        "app.workers.attempt_worker"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])


# Celery Beat Schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    "sync-leaderboard-every-5-minutes": {
        "task": "app.workers.leaderboard_worker.sync_leaderboard_to_db",
        "schedule": 300.0,  # 5 minutes
    },
    "auto-submit-expired-attempts-every-minute": {
        "task": "app.workers.attempt_worker.auto_submit_expired_attempts",
        "schedule": 60.0,  # 1 minute
    },
}
