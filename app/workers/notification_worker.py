"""Notification worker for sending emails and notifications"""

from uuid import UUID
from app.workers.celery_app import celery_app
from app.db.session import async_session_maker
from app.services.notification_service import NotificationService
from app.repositories.quiz_repo import QuizRepository
from app.repositories.user_repo import UserRepository
import logging
import asyncio

logger = logging.getLogger(__name__)


@celery_app.task(name="notifications.send_quiz_published")
def send_quiz_published(quiz_id: str) -> None:
    """Celery task to send quiz published notifications."""
    
    async def _send() -> None:
        async with async_session_maker() as db:
            quiz_repo = QuizRepository(db)
            user_repo = UserRepository(db)
            notification_service = NotificationService(quiz_repo, user_repo)
            
            await notification_service.send_quiz_published_notification(
                UUID(quiz_id)
            )
    
    asyncio.run(_send())
    logger.info(f"Quiz published notification task completed for quiz {quiz_id}")


@celery_app.task(name="notifications.send_result_notification")
def send_result_notification(
    user_id: str,
    quiz_id: str,
    score: int,
    percentage: float,
    passed: bool
) -> None:
    """Celery task to send result notification."""
    
    async def _send() -> None:
        async with async_session_maker() as db:
            quiz_repo = QuizRepository(db)
            user_repo = UserRepository(db)
            notification_service = NotificationService(quiz_repo, user_repo)
            
            await notification_service.send_result_notification(
                UUID(user_id),
                UUID(quiz_id),
                score,
                percentage,
                passed
            )
    
    asyncio.run(_send())
    logger.info(f"Result notification task completed for user {user_id}")


@celery_app.task(name="notifications.send_quiz_assigned")
def send_quiz_assigned(user_id: str, quiz_id: str) -> None:
    """Celery task to send quiz assignment notification."""
    
    async def _send() -> None:
        async with async_session_maker() as db:
            quiz_repo = QuizRepository(db)
            user_repo = UserRepository(db)
            notification_service = NotificationService(quiz_repo, user_repo)
            
            await notification_service.send_quiz_assigned_notification(
                UUID(user_id),
                UUID(quiz_id)
            )
    
    asyncio.run(_send())
    logger.info(f"Quiz assignment notification task completed for user {user_id}")
