"""
LangGraph State Schema
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class AgentState(TypedDict, total=False):
    """
    Shared state schema for multi-agent workflow
    
    This state is passed between all agents in the LangGraph workflow
    """
    # Core identifiers
    user_id: str
    event_id: str
    workflow_id: str
    
    # Event information
    event_name: str
    event_description: str
    event_type: str
    event_theme: str
    target_audience: str
    start_date: datetime
    end_date: datetime
    
    # Participant data
    participants: List[Dict[str, Any]]
    participant_count: int
    speakers: List[Dict[str, Any]]
    sponsors: List[Dict[str, Any]]
    
    # Schedule data
    schedule: Dict[str, Any]
    scheduled_sessions: List[Dict[str, Any]]
    rooms: List[str]
    schedule_conflicts: List[Dict[str, Any]]
    
    # Marketing data
    marketing_posts: List[Dict[str, Any]]
    marketing_plan: Dict[str, Any]
    marketing_timeline: List[Dict[str, Any]]
    
    # Email data
    emails_sent: List[Dict[str, Any]]
    email_templates: Dict[str, str]
    email_segments: Dict[str, List[Dict[str, Any]]]
    
    # Analytics data
    analytics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    engagement_metrics: Dict[str, Any]
    
    # Agent execution tracking
    current_agent: str
    completed_agents: List[str]
    agent_outputs: Dict[str, Any]
    
    # Error handling
    errors: List[str]
    warnings: List[str]
    
    # Workflow control
    should_continue: bool
    next_agent: Optional[str]
    
    # Memory and context
    context: Dict[str, Any]
    retrieved_memories: List[Dict[str, Any]]
    
    # Metadata
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class WorkflowConfig(TypedDict, total=False):
    """Configuration for workflow execution"""
    # Agent selection
    enable_content_agent: bool
    enable_email_agent: bool
    enable_scheduler_agent: bool
    enable_analytics_agent: bool
    
    # Execution parameters
    max_iterations: int
    timeout_seconds: int
    parallel_execution: bool
    
    # Agent-specific configs
    content_agent_config: Dict[str, Any]
    email_agent_config: Dict[str, Any]
    scheduler_agent_config: Dict[str, Any]
    analytics_agent_config: Dict[str, Any]
    
    # Memory configuration
    use_vector_memory: bool
    memory_k: int
    
    # Output preferences
    save_to_database: bool
    return_detailed_logs: bool


def create_initial_state(
    user_id: str,
    event_id: str,
    event_data: Dict[str, Any]
) -> AgentState:
    """
    Create initial agent state
    
    Args:
        user_id: User ID
        event_id: Event ID
        event_data: Event information
        
    Returns:
        Initial AgentState
    """
    from uuid import uuid4
    
    return AgentState(
        # Core identifiers
        user_id=user_id,
        event_id=event_id,
        workflow_id=str(uuid4()),
        
        # Event information
        event_name=event_data.get("name", ""),
        event_description=event_data.get("description", ""),
        event_type=event_data.get("event_type", ""),
        event_theme=event_data.get("theme", ""),
        target_audience=event_data.get("target_audience", ""),
        start_date=event_data.get("start_date"),
        end_date=event_data.get("end_date"),
        
        # Initialize empty collections
        participants=[],
        participant_count=0,
        speakers=[],
        sponsors=[],
        
        schedule={},
        scheduled_sessions=[],
        rooms=[],
        schedule_conflicts=[],
        
        marketing_posts=[],
        marketing_plan={},
        marketing_timeline=[],
        
        emails_sent=[],
        email_templates={},
        email_segments={},
        
        analytics={},
        insights=[],
        recommendations=[],
        engagement_metrics={},
        
        # Agent tracking
        current_agent="",
        completed_agents=[],
        agent_outputs={},
        
        # Error handling
        errors=[],
        warnings=[],
        
        # Workflow control
        should_continue=True,
        next_agent=None,
        
        # Memory
        context={},
        retrieved_memories=[],
        
        # Metadata
        metadata=event_data.get("event_metadata", {}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


def get_default_config() -> WorkflowConfig:
    """
    Get default workflow configuration
    
    Returns:
        Default WorkflowConfig
    """
    return WorkflowConfig(
        # Enable all agents by default
        enable_content_agent=True,
        enable_email_agent=True,
        enable_scheduler_agent=True,
        enable_analytics_agent=True,
        
        # Execution parameters
        max_iterations=10,
        timeout_seconds=300,
        parallel_execution=False,
        
        # Agent configs
        content_agent_config={
            "platforms": ["twitter", "linkedin", "facebook"],
            "posts_per_platform": 3
        },
        email_agent_config={
            "batch_size": 50,
            "send_immediately": False
        },
        scheduler_agent_config={
            "auto_resolve_conflicts": True,
            "buffer_minutes": 15
        },
        analytics_agent_config={
            "analysis_types": ["engagement", "demographics"]
        },
        
        # Memory
        use_vector_memory=True,
        memory_k=3,
        
        # Output
        save_to_database=True,
        return_detailed_logs=True
    )