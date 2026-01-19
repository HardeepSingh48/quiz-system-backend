"""Repository for notification data access"""

from uuid import UUID
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.base import Notification
from datetime import datetime, timedelta
from typing import Optional


class NotificationRepository:
    """Repository for notification data access."""
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def create(self, notification: Notification) -> Notification:
        """Create a new notification."""
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification
    
    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Get notification by ID."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> list[Notification]:
        """
        Get all notifications for a user.
        Ordered by created_at descending (newest first).
        """
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications for a user."""
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))
    
    async def mark_as_read(self, notification_id: UUID) -> Optional[Notification]:
        """Mark a notification as read."""
        notification = await self.get_by_id(notification_id)
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.session.add(notification)
            await self.session.commit()
            await self.session.refresh(notification)
        return notification
    
    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.
        Returns count of notifications marked.
        """
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        notifications = list(result.scalars().all())
        
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.session.add(notification)
        
        await self.session.commit()
        return len(notifications)
    
    async def delete_old_notifications(self, days: int) -> int:
        """
        Delete notifications older than specified days.
        Returns count of deleted notifications.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(Notification).where(Notification.created_at < cutoff_date)
        result = await self.session.execute(stmt)
        notifications = list(result.scalars().all())
        
        for notification in notifications:
            await self.session.delete(notification)
        
        await self.session.commit()
        return len(notifications)
    
    async def delete_by_id(self, notification_id: UUID) -> bool:
        """Delete a notification by ID."""
        notification = await self.get_by_id(notification_id)
        if notification:
            await self.session.delete(notification)
            await self.session.commit()
            return True
        return False
