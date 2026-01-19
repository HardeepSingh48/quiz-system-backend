"""Domain enumerations for the Online Quiz System"""

from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"


class QuestionType(str, Enum):
    """Types of questions supported"""
    MCQ = "mcq"  # Multiple Choice Question
    TRUE_FALSE = "true_false"


class AttemptStatus(str, Enum):
    """Quiz attempt statuses"""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"
