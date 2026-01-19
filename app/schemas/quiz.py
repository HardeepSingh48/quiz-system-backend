"""Pydantic schemas for quizzes and questions"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.domain.enums import QuestionType


class QuestionCreate(BaseModel):
    """Schema for creating a question"""
    question_text: str = Field(min_length=5)
    question_type: QuestionType
    options: List[str] = Field(min_items=2)
    correct_answer: str
    points: int = Field(default=1, gt=0)
    order: int = Field(ge=0)
    
    @validator("correct_answer")
    def validate_correct_answer(cls, v: str, values: dict) -> str:
        """Validate that correct answer is in options"""
        if "options" in values and v not in values["options"]:
            raise ValueError("Correct answer must be one of the options")
        return v


class QuestionResponse(BaseModel):
    """Schema for question response"""
    id: UUID
    question_text: str
    question_type: QuestionType
    options: List[str]
    points: int
    order: int
    
    class Config:
        from_attributes = True


class QuestionWithAnswer(QuestionResponse):
    """Schema for question with correct answer (admin only)"""
    correct_answer: str


class QuizCreate(BaseModel):
    """Schema for creating a quiz"""
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=10)
    duration_minutes: int = Field(gt=0, le=300)  # Max 5 hours
    passing_score: int = Field(ge=0, le=100)
    randomize_questions: bool = Field(default=False)
    randomize_options: bool = Field(default=False)
    max_attempts: Optional[int] = Field(default=None, ge=1)
    questions: List[QuestionCreate] = Field(min_items=1)


class QuizUpdate(BaseModel):
    """Schema for updating a quiz"""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    duration_minutes: Optional[int] = Field(None, gt=0, le=300)
    passing_score: Optional[int] = Field(None, ge=0, le=100)
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    max_attempts: Optional[int] = Field(None, ge=1)


class QuizResponse(BaseModel):
    """Schema for quiz response (for users)"""
    id: UUID
    title: str
    description: str
    duration_minutes: int
    passing_score: int
    is_published: bool
    max_attempts: Optional[int]
    created_at: datetime
    questions: List[QuestionResponse]
    
    class Config:
        from_attributes = True


class QuizAdminResponse(QuizResponse):
    """Schema for quiz response with answers (admin only)"""
    questions: List[QuestionWithAnswer]
    created_by: UUID
    randomize_questions: bool
    randomize_options: bool


class QuizListItem(BaseModel):
    """Schema for quiz list item"""
    id: UUID
    title: str
    description: str
    duration_minutes: int
    passing_score: int
    is_published: bool
    created_at: datetime
    question_count: int
    
    class Config:
        from_attributes = True
