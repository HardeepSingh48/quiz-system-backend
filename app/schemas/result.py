"""Pydantic schemas for quiz results"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class ResultResponse(BaseModel):
    """Schema for quiz result response"""
    id: UUID
    attempt_id: UUID
    quiz_id: UUID
    user_id: UUID
    score: int
    total_points: int
    percentage: float
    passed: bool
    rank: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Schema for leaderboard entry"""
    rank: int
    user_id: UUID
    username: str
    score: int
    total_points: int
    percentage: float
    submitted_at: datetime
    
    class Config:
        from_attributes = True


class UserResultSummary(BaseModel):
    """Schema for user's result summary"""
    quiz_id: UUID
    quiz_title: str
    attempt_count: int
    best_score: int
    best_percentage: float
    passed: bool
    last_attempt_at: datetime
