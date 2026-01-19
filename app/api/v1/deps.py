"""FastAPI dependencies for dependency injection"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.base import User
from app.repositories.user_repo import UserRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.result_repo import ResultRepository
from app.services.auth_service import AuthService
from app.services.quiz_service import QuizService
from app.services.attempt_service import AttemptService
from app.services.scoring_service import ScoringService
from app.domain.enums import UserRole
from app.core.exceptions import InvalidTokenException, InsufficientPermissionsException

# Security scheme
security = HTTPBearer()


# Repository dependencies
def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository"""
    return UserRepository(db)


def get_quiz_repo(db: AsyncSession = Depends(get_db)) -> QuizRepository:
    """Get quiz repository"""
    return QuizRepository(db)


def get_attempt_repo(db: AsyncSession = Depends(get_db)) -> AttemptRepository:
    """Get attempt repository"""
    return AttemptRepository(db)


def get_result_repo(db: AsyncSession = Depends(get_db)) -> ResultRepository:
    """Get result repository"""
    return ResultRepository(db)


# Service dependencies
def get_auth_service(user_repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    """Get authentication service"""
    return AuthService(user_repo)


def get_quiz_service(quiz_repo: QuizRepository = Depends(get_quiz_repo)) -> QuizService:
    """Get quiz service"""
    return QuizService(quiz_repo)


def get_scoring_service(
    attempt_repo: AttemptRepository = Depends(get_attempt_repo),
    quiz_repo: QuizRepository = Depends(get_quiz_repo)
) -> ScoringService:
    """Get scoring service"""
    return ScoringService(attempt_repo, quiz_repo)


def get_attempt_service(
    attempt_repo: AttemptRepository = Depends(get_attempt_repo),
    quiz_repo: QuizRepository = Depends(get_quiz_repo),
    result_repo: ResultRepository = Depends(get_result_repo),
    scoring_service: ScoringService = Depends(get_scoring_service)
) -> AttemptService:
    """Get attempt service"""
    return AttemptService(attempt_repo, quiz_repo, result_repo, scoring_service)


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP bearer credentials
        auth_service: Authentication service
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role
    
    Args:
        current_user: Current user
        
    Returns:
        Current user (if admin)
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user
    
    Args:
        current_user: Current user
        
    Returns:
        Current user (if active)
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user
