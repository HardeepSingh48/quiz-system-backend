"""Notification service for handling email and push notifications"""

from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.repositories.quiz_repo import QuizRepository
from app.repositories.user_repo import UserRepository
from app.db.base import Quiz, User
from typing import List
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling all notification operations."""
    
    def __init__(
        self,
        quiz_repo: QuizRepository,
        user_repo: UserRepository
    ) -> None:
        self.quiz_repo = quiz_repo
        self.user_repo = user_repo
    
    async def send_quiz_published_notification(
        self,
        quiz_id: UUID
    ) -> None:
        """
        Send notification when a quiz is published.
        In production, this would send actual emails.
        """
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=False)
        if not quiz:
            logger.error(f"Quiz {quiz_id} not found for notification")
            return
        
        # Get all assigned users
        assignments = await self.quiz_repo.get_quiz_assignments(quiz_id)
        
        logger.info(f"Sending quiz published notifications for: {quiz.title}")        
        for assignment, user in assignments:
            if user and user.is_active:
                await self._send_email(
                    to=user.email,
                    subject=f"New Quiz Published: {quiz.title}",
                    body=self._render_quiz_published_email(user, quiz)
                )
                logger.info(f"  ✓ Sent to {user.email}")
    
    async def send_result_notification(
        self,
        user_id: UUID,
        quiz_id: UUID,
        score: int,
        percentage: float,
        passed: bool
    ) -> None:
        """Send notification when quiz result is available."""
        user = await self.user_repo.get_by_id(user_id)
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=False)
        
        if not user or not quiz:
            logger.error("User or quiz not found for result notification")
            return
        
        await self._send_email(
            to=user.email,
            subject=f"Quiz Result: {quiz.title}",
            body=self._render_result_email(user, quiz, score, percentage, passed)
        )
        logger.info(f"Result notification sent to {user.email}")
    
    async def send_quiz_assigned_notification(
        self,
        user_id: UUID,
        quiz_id: UUID
    ) -> None:
        """Send notification when a quiz is assigned to a user."""
        user = await self.user_repo.get_by_id(user_id)
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=False)
        
        if not user or not quiz:
            logger.error("User or quiz not found for assignment notification")
            return
        
        await self._send_email(
            to=user.email,
            subject=f"Quiz Assigned: {quiz.title}",
            body=self._render_quiz_assigned_email(user, quiz)
        )
        logger.info(f"Quiz assignment notification sent to {user.email}")
    
    async def _send_email(
        self,
        to: str,
        subject: str,
        body: str
    ) -> None:
        """
        Send email using SMTP.
        In production, integrate with SendGrid, AWS SES, etc.
        For now, we just log the email.
        """
        logger.info(f"📧 [EMAIL] To: {to}")
        logger.info(f"📧 [EMAIL] Subject: {subject}")
        logger.info(f"📧 [EMAIL] Body preview: {body[:100]}...")
        
        # TODO: Implement actual email sending with SMTP
        # from app.core.config import settings
        # import smtplib
        # from email.mime.text import MIMEText
        # ...
    
    def _render_quiz_published_email(self, user: User, quiz: Quiz) -> str:
        """Render quiz published email template."""
        return f"""
Hello {user.username},

A new quiz has been published: {quiz.title}

Description: {quiz.description}
Duration: {quiz.duration_minutes} minutes
Passing Score: {quiz.passing_score}%

Login to the Quiz System to start the quiz!

Best regards,
Quiz System Team
        """.strip()
    
    def _render_result_email(
        self,
        user: User,
        quiz: Quiz,
        score: int,
        percentage: float,
        passed: bool
    ) -> str:
        """Render result notification email template."""
        status = "PASSED ✅" if passed else "FAILED ❌"
        return f"""
Hello {user.username},

Your quiz result is ready!

Quiz: {quiz.title}
Score: {score} points
Percentage: {percentage:.2f}%
Status: {status}

Login to view detailed results and feedback.

Best regards,
Quiz System Team
        """.strip()
    
    def _render_quiz_assigned_email(self, user: User, quiz: Quiz) -> str:
        """Render quiz assignment email template."""
        return f"""
Hello {user.username},

You have been assigned a new quiz: {quiz.title}

Description: {quiz.description}
Duration: {quiz.duration_minutes} minutes
Passing Score: {quiz.passing_score}%

Login to the Quiz System to start the quiz!

Best regards,
Quiz System Team
        """.strip()
