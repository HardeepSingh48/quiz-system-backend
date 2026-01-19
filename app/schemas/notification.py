"""Pydantic schemas for notifications"""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class NotificationResponse(BaseModel):
    """Response schema for a notification."""
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    quiz_id: Optional[UUID] = None
    attempt_id: Optional[UUID] = None
    result_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Response schema for list of notifications with pagination."""
    notifications: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class UnreadCountResponse(BaseModel):
    """Response schema for unread notification count."""
    count: int
