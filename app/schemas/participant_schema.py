"""
Participant Schemas
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ParticipantBase(BaseModel):
    """Base participant schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    organization: Optional[str] = None
    role: Optional[str] = None
    is_speaker: bool = False
    is_sponsor: bool = False


class ParticipantCreate(ParticipantBase):
    """Participant creation schema"""
    event_id: UUID
    tags: Optional[list[str]] = None
    participant_metadata: Optional[Dict[str, Any]] = None


class ParticipantBulkCreate(BaseModel):
    """Bulk participant creation schema"""
    event_id: UUID
    participants: list[ParticipantBase]


class ParticipantUpdate(BaseModel):
    """Participant update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization: Optional[str] = None
    role: Optional[str] = None
    is_speaker: Optional[bool] = None
    is_sponsor: Optional[bool] = None
    tags: Optional[list[str]] = None
    participant_metadata: Optional[Dict[str, Any]] = None


class ParticipantResponse(ParticipantBase):
    """Participant response schema"""
    id: UUID
    event_id: UUID
    tags: Optional[list[str]] = None
    participant_metadata: Optional[Dict[str, Any]] = None
    registered_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CSVUploadResponse(BaseModel):
    """CSV upload response schema"""
    total_rows: int
    successful: int
    failed: int
    errors: list[str] = []
    participants: list[ParticipantResponse] = []