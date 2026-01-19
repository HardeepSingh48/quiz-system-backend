"""Pydantic schemas for quiz assignments"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class QuizAssignmentCreate(BaseModel):
    """Schema for assigning quiz to users"""
    user_ids: list[UUID] = Field(min_length=1)
    due_date: Optional[datetime] = None


class QuizAssignmentResponse(BaseModel):
    """Schema for quiz assignment response"""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    assigned_by: UUID
    assigned_at: datetime
    due_date: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class QuizAssignmentWithUser(BaseModel):
    """Schema for assignment with user details"""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    user_email: str
    user_username: str
    assigned_at: datetime
    due_date: Optional[datetime]
    is_active: bool
