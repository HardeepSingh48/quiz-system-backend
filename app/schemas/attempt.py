"""Pydantic schemas for quiz attempts"""

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.domain.enums import AttemptStatus


class AttemptStart(BaseModel):
    """Schema for starting a quiz attempt"""
    quiz_id: UUID


class AnswerSubmit(BaseModel):
    """Schema for submitting an answer"""
    question_id: UUID
    selected_answer: str


class AnswerResponse(BaseModel):
    """Schema for answer response"""
    id: UUID
    question_id: UUID
    selected_answer: str
    answered_at: datetime
    
    class Config:
        from_attributes = True


class AttemptResponse(BaseModel):
    """Schema for attempt response"""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime]
    is_submitted: bool
    status: AttemptStatus
    time_remaining_seconds: int
    answers: List[AnswerResponse]
    
    class Config:
        from_attributes = True


class AttemptSubmit(BaseModel):
    """Schema for submitting a quiz attempt"""
    pass  # No data needed, just trigger submission
