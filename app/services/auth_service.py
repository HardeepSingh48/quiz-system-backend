"""Authentication service with JWT token rotation"""

from datetime import datetime, timedelta
from typing import Tuple
from uuid import UUID
from jose import JWTError
from app.repositories.user_repo import UserRepository
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token
)
from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    InvalidTokenException,
    TokenExpiredException
)
from app.db.base import User


class AuthService:
    """Service for authentication operations"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register(
        self,
        email: str,
        username: str,
        password: str
    ) -> User:
        """
        Register a new user - always creates with 'user' role
        
        SECURITY: Role is hardcoded to 'user'. Admin users must be created via seed script.
        
        Args:
            email: User email
            username: Username
            password: Plain password
            
        Returns:
            Created user with role='user'
            
        Raises:
            UserAlreadyExistsException: If email or username exists
        """
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsException(
                details={"email": email, "reason": "Email already registered"}
            )
        
        existing_user = await self.user_repo.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsException(
                details={"username": username, "reason": "Username already taken"}
            )
        
        # Create user with FORCED 'user' role
        user = await self.user_repo.create(email, username, password, role="user")
        return user
    
    async def login(self, email: str, password: str) -> Tuple[str, str, int]:
        """
        Login user and return tokens
        
        Args:
            email: User email
            password: Plain password
            
        Returns:
            Tuple of (access_token, refresh_token, expires_in)
            
        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        # Verify user exists
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Store hashed refresh token
        token_hash = hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.create_refresh_token(user.id, token_hash, expires_at)
        
        return access_token, refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str, int]:
        """
        Refresh access token using refresh token (with rotation)
        
        Args:
            refresh_token: Current refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token, expires_in)
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token is expired
        """
        try:
            # Decode refresh token
            payload = decode_token(refresh_token)
            user_id = UUID(payload.get("sub"))
            
            # Verify token exists in database and is not revoked
            token_hash = hash_token(refresh_token)
            db_token = await self.user_repo.get_refresh_token(token_hash)
            
            if not db_token:
                raise InvalidTokenException(
                    message="Refresh token not found or already revoked"
                )
            
            # Check expiration
            if db_token.expires_at < datetime.utcnow():
                await self.user_repo.revoke_refresh_token(token_hash)
                raise TokenExpiredException()
            
            # Get user
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise InvalidTokenException(message="User not found")
            
            # Revoke old refresh token (rotation)
            await self.user_repo.revoke_refresh_token(token_hash)
            
            # Generate new tokens
            new_access_token = create_access_token(
                data={"sub": str(user.id), "role": user.role}
            )
            new_refresh_token = create_refresh_token(
                data={"sub": str(user.id)}
            )
            
            # Store new hashed refresh token
            new_token_hash = hash_token(new_refresh_token)
            new_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            await self.user_repo.create_refresh_token(user.id, new_token_hash, new_expires_at)
            
            return new_access_token, new_refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            
        except JWTError:
            raise InvalidTokenException(message="Invalid or malformed token")
    
    async def logout(self, user_id: UUID) -> None:
        """
        Logout user by revoking all refresh tokens
        
        Args:
            user_id: User ID
        """
        await self.user_repo.revoke_all_user_tokens(user_id)
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token
        
        Args:
            token: Access token
            
        Returns:
            User object
            
        Raises:
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token is expired
        """
        try:
            payload = decode_token(token)
            user_id = UUID(payload.get("sub"))
            
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise InvalidTokenException(message="User not found")
            
            return user
            
        except JWTError:
            raise InvalidTokenException(message="Invalid or malformed token")
