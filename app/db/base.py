"""Database models using SQLModel"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from app.domain.enums import UserRole, QuestionType, AttemptStatus


class User(SQLModel, table=True):
    """User model with authentication and RBAC"""
    
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    quizzes: List["Quiz"] = Relationship(back_populates="creator")
    attempts: List["Attempt"] = Relationship(back_populates="user")
    results: List["Result"] = Relationship(back_populates="user")
    refresh_tokens: List["RefreshToken"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")


class Quiz(SQLModel, table=True):
    """Quiz model with configuration"""
    
    __tablename__ = "quizzes"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=255)
    description: str
    duration_minutes: int = Field(gt=0)
    passing_score: int = Field(ge=0)
    
    # Access Control (NEW)
    is_public: bool = Field(default=False)  # Public quizzes accessible to all
    requires_enrollment: bool = Field(default=False)  # User must enroll first
    
    is_published: bool = Field(default=False)
    randomize_questions: bool = Field(default=False)
    randomize_options: bool = Field(default=False)
    max_attempts: Optional[int] = Field(default=None, ge=1)
    created_by: UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    creator: User = Relationship(back_populates="quizzes")
    questions: List["Question"] = Relationship(
        back_populates="quiz",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    attempts: List["Attempt"] = Relationship(back_populates="quiz")
    results: List["Result"] = Relationship(back_populates="quiz")
    assignments: List["QuizAssignment"] = Relationship(back_populates="quiz")


class Question(SQLModel, table=True):
    """Question model for quizzes"""
    
    __tablename__ = "questions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id")
    question_text: str
    question_type: QuestionType
    options: List[str] = Field(sa_column=Column(JSON))  # JSON list of options
    correct_answer: str = Field()  # Stored as string (for MCQ: option text, for T/F: "true" or "false")
    points: int = Field(default=1, gt=0)
    order: int = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    quiz: Quiz = Relationship(back_populates="questions")
    answers: List["Answer"] = Relationship(back_populates="question")


class Attempt(SQLModel, table=True):
    """Quiz attempt model with timing"""
    
    __tablename__ = "attempts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    submitted_at: Optional[datetime] = Field(default=None)
    is_submitted: bool = Field(default=False)
    time_taken_seconds: Optional[int] = Field(default=None)
    status: AttemptStatus = Field(default=AttemptStatus.IN_PROGRESS, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    quiz: Quiz = Relationship(back_populates="attempts")
    user: User = Relationship(back_populates="attempts")
    answers: List["Answer"] = Relationship(
        back_populates="attempt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    result: Optional["Result"] = Relationship(back_populates="attempt")


class Answer(SQLModel, table=True):
    """User's answer to a question"""
    
    __tablename__ = "answers"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    attempt_id: UUID = Field(foreign_key="attempts.id", index=True)
    question_id: UUID = Field(foreign_key="questions.id", index=True)
    selected_answer: str  # User's selected option
    is_correct: Optional[bool] = Field(default=None)
    answered_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    attempt: Attempt = Relationship(back_populates="answers")
    question: Question = Relationship(back_populates="answers")


class Result(SQLModel, table=True):
    """Quiz result model"""
    
    __tablename__ = "results"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    attempt_id: UUID = Field(foreign_key="attempts.id", unique=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id", index=True)
    score: int = Field(ge=0)
    total_points: int = Field(gt=0)
    percentage: float = Field(ge=0.0, le=100.0)
    passed: bool
    rank: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    attempt: Attempt = Relationship(back_populates="result")
    user: User = Relationship(back_populates="results")
    quiz: Quiz = Relationship(back_populates="results")


class RefreshToken(SQLModel, table=True):
    """Refresh token storage for JWT token rotation"""
    
    __tablename__ = "refresh_tokens"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(unique=True, index=True, max_length=64)  # SHA-256 hash
    expires_at: datetime
    is_revoked: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="refresh_tokens")


class QuizAssignment(SQLModel, table=True):
    """
    Tracks which users are assigned to which quizzes.
    Enables admin to control who can access specific quizzes.
    """
    
    __tablename__ = "quiz_assignments"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    quiz_id: UUID = Field(foreign_key="quizzes.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    assigned_by: UUID = Field(foreign_key="users.id")  # Admin who assigned
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = Field(default=None)  # Optional deadline
    is_active: bool = Field(default=True)
    
    # Relationships
    quiz: Quiz = Relationship(back_populates="assignments")
    user: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[QuizAssignment.user_id]"}
    )


class Notification(SQLModel, table=True):
    """
    In-app notification model.
    Stores all user notifications for display in the UI.
    """
    
    __tablename__ = "notifications"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    # Notification content
    type: str = Field(index=True, max_length=50)  # NotificationType enum value
    title: str = Field(max_length=255)
    message: str
    
    # Optional reference to related entity
    quiz_id: Optional[UUID] = Field(default=None, foreign_key="quizzes.id")
    attempt_id: Optional[UUID] = Field(default=None, foreign_key="attempts.id")
    result_id: Optional[UUID] = Field(default=None, foreign_key="results.id")
    
    # Status
    is_read: bool = Field(default=False, index=True)
    read_at: Optional[datetime] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    user: User = Relationship(back_populates="notifications")
    quiz: Optional[Quiz] = Relationship()
    attempt: Optional[Attempt] = Relationship()
    result: Optional[Result] = Relationship()
