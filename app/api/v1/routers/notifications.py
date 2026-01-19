"""API router for notifications"""

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.v1.deps import get_db, get_current_user
from app.services.notification_service import NotificationService
from app.repositories.notification_repo import NotificationRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.user_repo import UserRepository
from app.db.base import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse
)
from uuid import UUID
from typing import Annotated

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Dependency to get notification service."""
    return NotificationService(
        session=db,
        notification_repo=NotificationRepository(db),
        quiz_repo=QuizRepository(db),
        user_repo=UserRepository(db)
    )


@router.get("/", response_model=NotificationListResponse)
async def get_my_notifications(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
) -> NotificationListResponse:
    """
    Get current user's notifications.
    Supports pagination and filtering by unread status.
    """
    notifications = await notification_service.get_user_notifications(
        current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    
    total = len(notifications)  # For simplicity; implement proper count if needed
    
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
) -> UnreadCountResponse:
    """Get count of unread notifications for current user."""
    count = await notification_service.get_unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
) -> NotificationResponse:
    """Mark a notification as read."""
    notification = await notification_service.mark_as_read(
        notification_id,
        current_user.id
    )
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
) -> dict[str, int]:
    """Mark all notifications as read for current user."""
    count = await notification_service.mark_all_as_read(current_user.id)
    return {"marked_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
) -> None:
    """Delete a notification."""
    deleted = await notification_service.delete_notification(
        notification_id,
        current_user.id
    )
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
