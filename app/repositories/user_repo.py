"""User repository for database operations"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.base import User, RefreshToken
from app.core.security import hash_password


class UserRepository:
    """Repository for User entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, email: str, username: str, password: str, role: str) -> User:
        """Create a new user"""
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            role=role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update(self, user: User) -> User:
        """Update user"""
        user.updated_at = datetime.utcnow()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    # Refresh Token Operations
    
    async def create_refresh_token(
        self, 
        user_id: UUID, 
        token_hash: str, 
        expires_at: datetime
    ) -> RefreshToken:
        """Create a refresh token"""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)
        return refresh_token
    
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash"""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Revoke a refresh token"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token:
            token.is_revoked = True
            self.session.add(token)
            await self.session.commit()
    
    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user"""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False
                )
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
            self.session.add(token)
        await self.session.commit()
