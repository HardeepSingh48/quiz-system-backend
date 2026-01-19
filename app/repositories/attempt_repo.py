"""Attempt repository for database operations"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.db.base import Attempt, Answer
from app.domain.enums import AttemptStatus


class AttemptRepository:
    """Repository for Attempt entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        quiz_id: UUID,
        user_id: UUID,
        expires_at: datetime
    ) -> Attempt:
        """Create a new quiz attempt"""
        attempt = Attempt(
            quiz_id=quiz_id,
            user_id=user_id,
            expires_at=expires_at,
            status=AttemptStatus.IN_PROGRESS
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt
    
    async def get_by_id(self, attempt_id: UUID, include_answers: bool = True) -> Optional[Attempt]:
        """Get attempt by ID"""
        query = select(Attempt).where(Attempt.id == attempt_id)
        
        if include_answers:
            query = query.options(selectinload(Attempt.answers))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_for_update(self, attempt_id: UUID) -> Optional[Attempt]:
        """Get attempt with row lock for update (prevents race conditions)"""
        result = await self.session.execute(
            select(Attempt)
            .where(Attempt.id == attempt_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()
    
    async def get_active_attempt(self, user_id: UUID, quiz_id: UUID) -> Optional[Attempt]:
        """Get active attempt for a user and quiz"""
        result = await self.session.execute(
            select(Attempt).where(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.quiz_id == quiz_id,
                    Attempt.status == AttemptStatus.IN_PROGRESS
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def count_user_attempts(self, user_id: UUID, quiz_id: UUID) -> int:
        """Count total attempts by user for a quiz"""
        result = await self.session.execute(
            select(Attempt).where(
                and_(
                    Attempt.user_id == user_id,
                    Attempt.quiz_id == quiz_id
                )
            )
        )
        return len(list(result.scalars().all()))
    
    async def update(self, attempt: Attempt) -> Attempt:
        """Update attempt"""
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt
    
    async def create_answer(
        self,
        attempt_id: UUID,
        question_id: UUID,
        selected_answer: str
    ) -> Answer:
        """Create or update an answer"""
        # Check if answer already exists
        result = await self.session.execute(
            select(Answer).where(
                and_(
                    Answer.attempt_id == attempt_id,
                    Answer.question_id == question_id
                )
            )
        )
        existing_answer = result.scalar_one_or_none()
        
        if existing_answer:
            # Update existing answer
            existing_answer.selected_answer = selected_answer
            existing_answer.answered_at = datetime.utcnow()
            self.session.add(existing_answer)
            await self.session.commit()
            await self.session.refresh(existing_answer)
            return existing_answer
        else:
            # Create new answer
            answer = Answer(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_answer=selected_answer
            )
            self.session.add(answer)
            await self.session.commit()
            await self.session.refresh(answer)
            return answer
    
    async def get_answers(self, attempt_id: UUID) -> List[Answer]:
        """Get all answers for an attempt"""
        result = await self.session.execute(
            select(Answer)
            .where(Answer.attempt_id == attempt_id)
            .options(selectinload(Answer.question))
        )
        return list(result.scalars().all())
    
    async def get_expired_attempts(self) -> List[Attempt]:
        """Get all expired but not submitted attempts"""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Attempt).where(
                and_(
                    Attempt.expires_at < now,
                    Attempt.status == AttemptStatus.IN_PROGRESS
                )
            )
        )
        return list(result.scalars().all())
