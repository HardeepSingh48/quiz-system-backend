"""Notification worker for in-app notifications"""

from uuid import UUID
from app.workers.celery_app import celery_app
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.services.notification_service import NotificationService
from app.repositories.notification_repo import NotificationRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.user_repo import UserRepository
import asyncio
import logging


async def run_with_db(callback):
    """Helper to run async code with a fresh DB connection in a new loop."""
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with AsyncSessionLocal() as db:
            await callback(db)
    finally:
        await engine.dispose()


@celery_app.task(name="notifications.send_quiz_published")
def send_quiz_published(quiz_id: str) -> None:
    """Celery task to create quiz published notifications."""
    
    async def _work(db: AsyncSession) -> None:
        notification_service = NotificationService(
            session=db,
            notification_repo=NotificationRepository(db),
            quiz_repo=QuizRepository(db),
            user_repo=UserRepository(db)
        )
        
        count = await notification_service.notify_quiz_published(UUID(quiz_id))
        logger.info(f"Created {count} quiz published notifications for quiz {quiz_id}")
    
    asyncio.run(run_with_db(_work))


@celery_app.task(name="notifications.send_quiz_assigned")
def send_quiz_assigned(user_id: str, quiz_id: str) -> None:
    """Celery task to create quiz assignment notification."""
    
    async def _work(db: AsyncSession) -> None:
        notification_service = NotificationService(
            session=db,
            notification_repo=NotificationRepository(db),
            quiz_repo=QuizRepository(db),
            user_repo=UserRepository(db)
        )
        
        await notification_service.notify_quiz_assigned(
            UUID(user_id),
            UUID(quiz_id)
        )
        logger.info(f"Created quiz assignment notification for user {user_id}")
    
    asyncio.run(run_with_db(_work))


@celery_app.task(name="notifications.send_result_notification")
def send_result_notification(
    user_id: str,
    quiz_id: str,
    result_id: str,
    score: int,
    percentage: float,
    passed: bool
) -> None:
    """Celery task to create result notification."""
    
    async def _work(db: AsyncSession) -> None:
        notification_service = NotificationService(
            session=db,
            notification_repo=NotificationRepository(db),
            quiz_repo=QuizRepository(db),
            user_repo=UserRepository(db)
        )
        
        await notification_service.notify_result_available(
            UUID(user_id),
            UUID(quiz_id),
            UUID(result_id),
            score,
            percentage,
            passed
        )
        logger.info(f"Created result notification for user {user_id}")
    
    asyncio.run(run_with_db(_work))


@celery_app.task(name="notifications.cleanup_old_notifications")
def cleanup_old_notifications() -> None:
    """Delete notifications older than 30 days."""
    
    async def _work(db: AsyncSession) -> None:
        notification_repo = NotificationRepository(db)
        count = await notification_repo.delete_old_notifications(30)
        logger.info(f"Cleaned up {count} old notifications")
    
    asyncio.run(run_with_db(_work))
