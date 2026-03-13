"""
Agent Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class AgentExecutionRequest(BaseModel):
    """Agent execution request schema"""
    event_id: UUID
    workflow_type: str = Field(..., description="Type of workflow to execute")
    parameters: Optional[Dict[str, Any]] = None


class AgentExecutionResponse(BaseModel):
    """Agent execution response schema"""
    workflow_id: UUID
    status: str
    message: str
    results: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None


class MarketingWorkflowRequest(BaseModel):
    """Marketing workflow request schema"""
    event_id: UUID
    generate_posts: bool = True
    generate_plan: bool = True
    platforms: Optional[List[str]] = ["twitter", "linkedin", "facebook"]


class EmailWorkflowRequest(BaseModel):
    """Email workflow request schema"""
    event_id: UUID
    participant_ids: Optional[List[UUID]] = None
    email_template: Optional[str] = None
    subject: Optional[str] = None
    send_immediately: bool = False


class SchedulerWorkflowRequest(BaseModel):
    """Scheduler workflow request schema"""
    event_id: UUID
    auto_resolve_conflicts: bool = True
    optimization_goals: Optional[List[str]] = ["minimize_conflicts", "maximize_utilization"]


class AnalyticsWorkflowRequest(BaseModel):
    """Analytics workflow request schema"""
    event_id: UUID
    analysis_types: Optional[List[str]] = ["engagement", "demographics", "trends"]
    generate_recommendations: bool = True


class AgentLogResponse(BaseModel):
    """Agent log response schema"""
    id: UUID
    event_id: Optional[UUID] = None
    agent_name: str
    workflow_id: Optional[UUID] = None
    status: str
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowStatusResponse(BaseModel):
    """Workflow status response schema"""
    workflow_id: UUID
    status: str
    progress: float = Field(..., ge=0.0, le=100.0)
    current_step: Optional[str] = None
    completed_steps: List[str] = []
    pending_steps: List[str] = []
    errors: List[str] = []