"""
Event Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.database.models import EventStatus


class EventBase(BaseModel):
    """Base event schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    theme: Optional[str] = None
    target_audience: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location: Optional[str] = None
    venue: Optional[str] = None
    max_participants: Optional[int] = Field(None, gt=0)


class EventCreate(EventBase):
    """Event creation schema"""
    event_metadata: Optional[Dict[str, Any]] = None


class EventUpdate(BaseModel):
    """Event update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    theme: Optional[str] = None
    target_audience: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    max_participants: Optional[int] = Field(None, gt=0)
    status: Optional[EventStatus] = None
    event_metadata: Optional[Dict[str, Any]] = None


class EventResponse(EventBase):
    """Event response schema"""
    id: UUID
    owner_id: UUID
    status: EventStatus
    event_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ScheduleBase(BaseModel):
    """Base schedule schema"""
    session_name: str = Field(..., min_length=1, max_length=255)
    session_type: Optional[str] = None
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: Optional[int] = None
    room: Optional[str] = None
    speaker: Optional[str] = None
    max_capacity: Optional[int] = None


class ScheduleCreate(ScheduleBase):
    """Schedule creation schema"""
    event_id: UUID
    tags: Optional[list[str]] = None
    schedule_metadata: Optional[Dict[str, Any]] = None


class ScheduleResponse(ScheduleBase):
    """Schedule response schema"""
    id: UUID
    event_id: UUID
    tags: Optional[list[str]] = None
    schedule_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MarketingPostBase(BaseModel):
    """Base marketing post schema"""
    platform: Optional[str] = None
    post_type: Optional[str] = None
    title: Optional[str] = None
    content: str
    hashtags: Optional[list[str]] = None
    scheduled_time: Optional[datetime] = None


class MarketingPostCreate(MarketingPostBase):
    """Marketing post creation schema"""
    event_id: UUID


class MarketingPostResponse(MarketingPostBase):
    """Marketing post response schema"""
    id: UUID
    event_id: UUID
    is_published: bool
    published_at: Optional[datetime] = None
    engagement_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)