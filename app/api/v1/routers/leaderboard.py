"""Leaderboard router"""

from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.schemas.result import LeaderboardEntry
from app.db.base import Result, User
from app.db.session import get_db
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.get("/quizzes/{quiz_id}", response_model=List[LeaderboardEntry])
async def get_quiz_leaderboard(
    quiz_id: UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard for a specific quiz
    
    Args:
        quiz_id: Quiz ID
        limit: Number of top results to return
        current_user: Current user
        db: Database session
        
    Returns:
        List of leaderboard entries
    """
    # Query top results with user information
    query = (
        select(Result, User)
        .join(User, Result.user_id == User.id)
        .where(Result.quiz_id == quiz_id)
        .order_by(desc(Result.score), Result.created_at)
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build leaderboard entries
    leaderboard = []
    for rank, (result_obj, user_obj) in enumerate(rows, start=1):
        leaderboard.append(
            LeaderboardEntry(
                rank=rank,
                user_id=user_obj.id,
                username=user_obj.username,
                score=result_obj.score,
                total_points=result_obj.total_points,
                percentage=result_obj.percentage,
                submitted_at=result_obj.created_at
            )
        )
    
    return leaderboard


@router.get("/global", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get global leaderboard (all quizzes)
    
    Args:
        limit: Number of top results to return
        current_user: Current user
        db: Database session
        
    Returns:
        List of leaderboard entries
    """
    # Query top results across all quizzes
    query = (
        select(Result, User)
        .join(User, Result.user_id == User.id)
        .order_by(desc(Result.score), Result.created_at)
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build leaderboard entries
    leaderboard = []
    for rank, (result_obj, user_obj) in enumerate(rows, start=1):
        leaderboard.append(
            LeaderboardEntry(
                rank=rank,
                user_id=user_obj.id,
                username=user_obj.username,
                score=result_obj.score,
                total_points=result_obj.total_points,
                percentage=result_obj.percentage,
                submitted_at=result_obj.created_at
            )
        )
    
    return leaderboard
