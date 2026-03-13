"""
Participant Management Routes
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import User, Event, Participant
from app.schemas.participant_schema import (
    ParticipantCreate,
    ParticipantResponse,
    ParticipantUpdate,
    CSVUploadResponse
)
from app.services.csv_parser import CSVParser
from app.dependencies import get_current_active_user
from app.utils.logger import logger


router = APIRouter(prefix="/participants", tags=["Participants"])


@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def create_participant(
    participant_data: ParticipantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new participant"""
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == participant_data.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Create participant
    new_participant = Participant(
        event_id=participant_data.event_id,
        email=participant_data.email,
        full_name=participant_data.full_name,
        organization=participant_data.organization,
        role=participant_data.role,
        is_speaker=participant_data.is_speaker,
        is_sponsor=participant_data.is_sponsor,
        tags=participant_data.tags or [],
        participant_metadata=participant_data.participant_metadata or {}
    )
    
    db.add(new_participant)
    await db.commit()
    await db.refresh(new_participant)
    
    logger.info(f"Participant created: {new_participant.full_name}")
    
    return new_participant


@router.get("/event/{event_id}", response_model=List[ParticipantResponse])
async def list_event_participants(
    event_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all participants for an event"""

    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Explicit query for participants
    result = await db.execute(
        select(Participant).where(Participant.event_id == event_id)
    )

    participants = result.scalars().all()

    return participants


@router.post("/upload-csv", response_model=CSVUploadResponse)
async def upload_participants_csv(
    event_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload participants via CSV file"""
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Read file content
    content = await file.read()
    
    # Parse CSV
    parser = CSVParser()
    participants_data, errors = parser.parse_csv_file(content)
    
    # Create participants
    created_participants = []
    for p_data in participants_data:
        try:
            participant = Participant(
                event_id=event_id,
                **p_data
            )
            db.add(participant)
            created_participants.append(participant)
        except Exception as e:
            errors.append(f"Failed to create participant {p_data.get('email')}: {str(e)}")
    
    await db.commit()
    
    # Refresh all created participants
    for p in created_participants:
        await db.refresh(p)
    
    logger.info(f"CSV upload: {len(created_participants)} participants created, {len(errors)} errors")
    
    return CSVUploadResponse(
        total_rows=len(participants_data) + len(errors),
        successful=len(created_participants),
        failed=len(errors),
        errors=errors,
        participants=created_participants
    )


@router.put("/{participant_id}", response_model=ParticipantResponse)
async def update_participant(
    participant_id: UUID,
    participant_data: ParticipantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a participant"""
    # Get participant and verify event ownership
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )
    
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == participant.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Update fields
    update_data = participant_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(participant, field, value)
    
    await db.commit()
    await db.refresh(participant)
    
    return participant


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_participant(
    participant_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a participant"""
    # Get participant and verify event ownership
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = result.scalar_one_or_none()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )
    
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == participant.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    await db.delete(participant)
    await db.commit()