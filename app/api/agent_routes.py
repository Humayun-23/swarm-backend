"""
Agent Workflow Routes
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database.session import get_db

from app.database.models import User, Event, Participant
from app.schemas.agent_schema import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentLogResponse,
    MarketingWorkflowRequest,
    EmailWorkflowRequest,
    SchedulerWorkflowRequest,
    AnalyticsWorkflowRequest
)
from app.orchestration import (
    event_workflow,
    create_initial_state,
    save_agent_logs_to_db
)
from app.agents import (
    content_agent,
    communication_agent,
    scheduler_agent,
    analytics_agent
)
from app.dependencies import get_current_active_user
from app.utils.logger import logger


router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.post("/workflow/run", response_model=AgentExecutionResponse)
async def run_full_workflow(
    request: AgentExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run complete multi-agent workflow
    
    Args:
        request: Workflow execution request
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Workflow execution response
    """
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == request.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get participants
    participants_result = await db.execute(
        select(Participant).where(Participant.event_id == request.event_id)
    )
    participants = participants_result.scalars().all()
    
    # Prepare event data for workflow
    event_data = {
        "name": event.name,
        "description": event.description,
        "event_type": event.event_type,
        "theme": event.theme,
        "target_audience": event.target_audience,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "location": event.location,
        "venue": event.venue,
        "metadata": event.event_metadata,
        "participants": [
            {
                "email": p.email,
                "full_name": p.full_name,
                "organization": p.organization,
                "role": p.role,
                "is_speaker": p.is_speaker,
                "is_sponsor": p.is_sponsor
            }
            for p in participants
        ],
        "participant_count": len(participants)
    }
    
    # Run workflow
    try:
        workflow_result = await event_workflow.run_workflow(
            user_id=str(current_user.id),
            event_id=str(event.id),
            event_data=event_data,
            config=request.parameters
        )
        
        # Save agent logs in background
        if workflow_result["status"] == "completed":
            background_tasks.add_task(
                save_agent_logs_to_db,
                db,
                str(event.id),
                workflow_result["workflow_id"],
                workflow_result["state"]
            )
            
            # Save generated content to database in background
            background_tasks.add_task(
                save_workflow_results,
                db,
                str(event.id),
                workflow_result["state"]
            )
        
        logger.info(f"Workflow {workflow_result['workflow_id']} completed for event {event.id}")
        
        return AgentExecutionResponse(
            workflow_id=UUID(workflow_result["workflow_id"]),
            status=workflow_result["status"],
            message="Workflow completed successfully" if workflow_result["status"] == "completed" else "Workflow failed",
            results={
                "scheduled_sessions": len(workflow_result["state"].get("scheduled_sessions", [])),
                "marketing_posts": len(workflow_result["state"].get("marketing_posts", [])),
                "emails_prepared": len(workflow_result["state"].get("emails_sent", [])),
                "insights": workflow_result["state"].get("insights", [])
            }
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/marketing/generate", response_model=AgentExecutionResponse)
async def generate_marketing_content(
    request: MarketingWorkflowRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate marketing content for event"""
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == request.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Create state for content agent
    state = create_initial_state(
        user_id=str(current_user.id),
        event_id=str(event.id),
        event_data={
            "name": event.name,
            "description": event.description,
            "event_type": event.event_type,
            "theme": event.theme,
            "target_audience": event.target_audience
        }
    )
    
    # Run content agent
    try:
        result_state = await content_agent.execute(state)
        
        return AgentExecutionResponse(
            workflow_id=UUID(result_state["workflow_id"]),
            status="completed",
            message="Marketing content generated successfully",
            results={
                "marketing_posts": result_state.get("marketing_posts", []),
                "marketing_plan": result_state.get("marketing_plan", {})
            }
        )
        
    except Exception as e:
        logger.error(f"Marketing content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/email/prepare", response_model=AgentExecutionResponse)
async def prepare_emails(
    request: EmailWorkflowRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Prepare personalized emails for participants"""
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == request.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Get participants
    participants_query = select(Participant).where(Participant.event_id == request.event_id)
    
    if request.participant_ids:
        participants_query = participants_query.where(
            Participant.id.in_(request.participant_ids)
        )
    
    participants_result = await db.execute(participants_query)
    participants = participants_result.scalars().all()
    
    # Create state
    state = create_initial_state(
        user_id=str(current_user.id),
        event_id=str(event.id),
        event_data={
            "name": event.name,
            "description": event.description,
            "participants": [
                {
                    "email": p.email,
                    "full_name": p.full_name,
                    "organization": p.organization,
                    "role": p.role,
                    "is_speaker": p.is_speaker,
                    "is_sponsor": p.is_sponsor
                }
                for p in participants
            ]
        }
    )
    
    # Run email agent
    try:
        result_state = await communication_agent.execute(state)
        
        # Optionally send emails immediately
        if request.send_immediately:
            send_stats = await communication_agent.send_emails(result_state, db)
        else:
            send_stats = {"prepared": len(result_state.get("emails_sent", []))}
        
        return AgentExecutionResponse(
            workflow_id=UUID(result_state["workflow_id"]),
            status="completed",
            message="Emails prepared successfully",
            results=send_stats
        )
        
    except Exception as e:
        logger.error(f"Email preparation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/schedule/generate", response_model=AgentExecutionResponse)
async def generate_schedule(
    request: SchedulerWorkflowRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate optimized event schedule"""
    # Verify event ownership
    result = await db.execute(
        select(Event).where(
            Event.id == request.event_id,
            Event.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Create state
    state = create_initial_state(
        user_id=str(current_user.id),
        event_id=str(event.id),
        event_data={
            "name": event.name,
            "start_date": event.start_date,
            "end_date": event.end_date,
            "venue": event.venue
        }
    )
    
    # Get speakers
    speakers_result = await db.execute(
        select(Participant).where(
            Participant.event_id == request.event_id,
            Participant.is_speaker == True
        )
    )
    speakers = speakers_result.scalars().all()
    state["speakers"] = [
        {"full_name": s.full_name, "organization": s.organization}
        for s in speakers
    ]
    
    # Run scheduler agent
    try:
        result_state = await scheduler_agent.execute(state)
        
        return AgentExecutionResponse(
            workflow_id=UUID(result_state["workflow_id"]),
            status="completed",
            message="Schedule generated successfully",
            results={
                "schedule": result_state.get("schedule", {}),
                "conflicts": result_state.get("schedule_conflicts", [])
            }
        )
        
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/analytics/generate", response_model=AgentExecutionResponse)
async def generate_analytics(
    request: AnalyticsWorkflowRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate analytics and insights"""

    # Verify event ownership
    stmt = (
        select(Event)
        .options(
            selectinload(Event.participants),
            selectinload(Event.schedules),
            selectinload(Event.marketing_posts),
        )
        .where(Event.id == request.event_id)
    )

    result = await db.execute(stmt)
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Get all event data
    participants = event.participants
    schedules = event.schedules
    marketing_posts = event.marketing_posts

    # Create state
    state = create_initial_state(
        user_id=str(current_user.id),
        event_id=str(event.id),
        event_data={"name": event.name}
    )

    state["participants"] = [
        {
            "email": p.email,
            "full_name": p.full_name,
            "organization": p.organization,
            "role": p.role,
            "is_speaker": p.is_speaker,
            "is_sponsor": p.is_sponsor
        }
        for p in participants
    ]

    state["participant_count"] = len(participants)

    state["scheduled_sessions"] = [
        {
            "session_name": s.session_name,
            "session_type": s.session_type,
            "duration_minutes": s.duration_minutes,
            "start_time": s.start_time,
            "end_time": s.end_time
        }
        for s in schedules
    ]

    state["marketing_posts"] = [
        {"platform": m.platform, "content": m.content}
        for m in marketing_posts
    ]

    # Run analytics agent
    try:
        result_state = await analytics_agent.execute(state)

        return AgentExecutionResponse(
            workflow_id=UUID(result_state["workflow_id"]),
            status="completed",
            message="Analytics generated successfully",
            results={
                "analytics": result_state.get("analytics", {}),
                "insights": result_state.get("insights", []),
                "recommendations": result_state.get("recommendations", [])
            }
        )

    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def save_workflow_results(
    db: AsyncSession,
    event_id: str,
    state: dict
):
    """Background task to save workflow results to database"""
    from app.database.models import Schedule, MarketingPost
    
    try:
        # Save schedules
        for session in state.get("scheduled_sessions", []):
            schedule = Schedule(
                event_id=event_id,
                session_name=session["session_name"],
                session_type=session.get("session_type"),
                description=session.get("description"),
                start_time=session["start_time"],
                end_time=session["end_time"],
                duration_minutes=session.get("duration_minutes"),
                room=session.get("room"),
                speaker=session.get("speaker")
            )
            db.add(schedule)
        
        # Save marketing posts
        for post in state.get("marketing_posts", []):
            marketing_post = MarketingPost(
                event_id=event_id,
                platform=post.get("platform"),
                post_type=post.get("post_type"),
                content=post["content"],
                hashtags=post.get("hashtags", [])
            )
            db.add(marketing_post)
        
        await db.commit()
        logger.info(f"Workflow results saved for event {event_id}")
        
    except Exception as e:
        logger.error(f"Failed to save workflow results: {e}")
        await db.rollback()