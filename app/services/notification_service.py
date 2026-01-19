"""Service for managing in-app notifications"""

from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.repositories.notification_repo import NotificationRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.user_repo import UserRepository
from app.db.base import Notification, Quiz, User
from app.domain.notification_types import NotificationType
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing in-app notifications."""
    
    def __init__(
        self,
        session: AsyncSession,
        notification_repo: Optional[NotificationRepository] = None,
        quiz_repo: Optional[QuizRepository] = None,
        user_repo: Optional[UserRepository] = None
    ) -> None:
        self.session = session
        self.notification_repo = notification_repo or NotificationRepository(session)
        self.quiz_repo = quiz_repo or QuizRepository(session)
        self.user_repo = user_repo or UserRepository(session)
    
    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        quiz_id: Optional[UUID] = None,
        attempt_id: Optional[UUID] = None,
        result_id: Optional[UUID] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            quiz_id=quiz_id,
            attempt_id=attempt_id,
            result_id=result_id
        )
        
        created = await self.notification_repo.create(notification)
        logger.info(f"Created notification {created.id} for user {user_id}")
        return created
    
    async def notify_quiz_published(self, quiz_id: UUID) -> int:
        """
        Create notifications for all assigned users when a quiz is published.
        Returns count of notifications created.
        """
        quiz: Optional[Quiz] = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            logger.error(f"Quiz {quiz_id} not found for notification")
            return 0
        
        # Get all assigned users
        assignments = await self.quiz_repo.get_quiz_assignments(quiz_id)
        
        count = 0
        for assignment in assignments:
            user: Optional[User] = await self.user_repo.get_by_id(assignment.user_id)
            if user and user.is_active:
                await self.create_notification(
                    user_id=user.id,
                    type=NotificationType.QUIZ_PUBLISHED,
                    title="New Quiz Published",
                    message=f"'{quiz.title}' is now available. Duration: {quiz.duration_minutes} min.",
                    quiz_id=quiz_id
                )
                count += 1
        
        logger.info(f"Created {count} quiz published notifications for quiz {quiz_id}")
        return count
    
    async def notify_quiz_assigned(
        self,
        user_id: UUID,
        quiz_id: UUID
    ) -> Notification:
        """Create notification when a quiz is assigned to a user."""
        quiz: Optional[Quiz] = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        user: Optional[User] = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return await self.create_notification(
            user_id=user_id,
            type=NotificationType.QUIZ_ASSIGNED,
            title="Quiz Assigned",
            message=f"You've been assigned '{quiz.title}'. Duration: {quiz.duration_minutes} min.",
            quiz_id=quiz_id
        )
    
    async def notify_result_available(
        self,
        user_id: UUID,
        quiz_id: UUID,
        result_id: UUID,
        score: int,
        percentage: float,
        passed: bool
    ) -> Notification:
        """Create notification when quiz result is available."""
        quiz: Optional[Quiz] = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        status_emoji = "✅" if passed else "❌"
        status_text = "Passed" if passed else "Failed"
        
        return await self.create_notification(
            user_id=user_id,
            type=NotificationType.RESULT_AVAILABLE,
            title=f"Quiz Result: {status_text}",
            message=f"{status_emoji} '{quiz.title}' - Score: {score} ({percentage:.1f}%)",
            quiz_id=quiz_id,
            result_id=result_id
        )
    
    async def notify_deadline_approaching(
        self,
        user_id: UUID,
        quiz_id: UUID,
        hours_remaining: int
    ) -> Notification:
        """Create notification when quiz deadline is approaching."""
        quiz: Optional[Quiz] = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        return await self.create_notification(
            user_id=user_id,
            type=NotificationType.QUIZ_DEADLINE_APPROACHING,
            title="Quiz Deadline Approaching",
            message=f"⏰ '{quiz.title}' is due in {hours_remaining} hours!",
            quiz_id=quiz_id
        )
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> list[Notification]:
        """Get all notifications for a user."""
        return await self.notification_repo.get_user_notifications(
            user_id, limit, offset, unread_only
        )
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        return await self.notification_repo.get_unread_count(user_id)
    
    async def mark_as_read(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> Optional[Notification]:
        """Mark notification as read (with user verification)."""
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            return None
        
        # Verify notification belongs to user
        if notification.user_id != user_id:
            raise PermissionError("Cannot mark another user's notification")
        
        return await self.notification_repo.mark_as_read(notification_id)
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        return await self.notification_repo.mark_all_as_read(user_id)
    
    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a notification (with user verification)."""
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            return False
        
        # Verify notification belongs to user
        if notification.user_id != user_id:
            raise PermissionError("Cannot delete another user's notification")
        
        return await self.notification_repo.delete_by_id(notification_id)
