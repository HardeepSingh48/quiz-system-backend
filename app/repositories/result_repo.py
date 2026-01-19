"""Result repository for database operations"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.db.base import Result


class ResultRepository:
    """Repository for Result entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        attempt_id: UUID,
        user_id: UUID,
        quiz_id: UUID,
        score: int,
        total_points: int,
        percentage: float,
        passed: bool
    ) -> Result:
        """Create a quiz result"""
        result = Result(
            attempt_id=attempt_id,
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_points=total_points,
            percentage=percentage,
            passed=passed
        )
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result
    
    async def get_by_id(self, result_id: UUID) -> Optional[Result]:
        """Get result by ID"""
        result = await self.session.execute(
            select(Result).where(Result.id == result_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_attempt_id(self, attempt_id: UUID) -> Optional[Result]:
        """Get result by attempt ID"""
        result = await self.session.execute(
            select(Result).where(Result.attempt_id == attempt_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_results(self, user_id: UUID) -> List[Result]:
        """Get all results for a user"""
        result = await self.session.execute(
            select(Result)
            .where(Result.user_id == user_id)
            .order_by(desc(Result.created_at))
        )
        return list(result.scalars().all())
    
    async def get_quiz_results(self, quiz_id: UUID) -> List[Result]:
        """Get all results for a quiz"""
        result = await self.session.execute(
            select(Result)
            .where(Result.quiz_id == quiz_id)
            .order_by(desc(Result.score))
        )
        return list(result.scalars().all())
    
    async def get_leaderboard(
        self, 
        quiz_id: UUID, 
        limit: int = 10
    ) -> List[Result]:
        """Get top results for a quiz"""
        result = await self.session.execute(
            select(Result)
            .where(Result.quiz_id == quiz_id)
            .order_by(desc(Result.score), Result.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_rank(self, result_id: UUID, rank: int) -> Optional[Result]:
        """Update result rank"""
        result = await self.get_by_id(result_id)
        if result:
            result.rank = rank
            self.session.add(result)
            await self.session.commit()
            await self.session.refresh(result)
        return result
