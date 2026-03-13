"""
Database Models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text,
    ForeignKey, Float, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

from app.database.session import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    ORGANIZER = "organizer"
    USER = "user"


class EventStatus(str, enum.Enum):
    """Event status enumeration"""
    DRAFT = "draft"
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmailStatus(str, enum.Enum):
    """Email status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


class Event(Base):
    """Event model"""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(100))
    theme = Column(String(255))
    target_audience = Column(Text)
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(500))
    venue = Column(String(255))
    
    max_participants = Column(Integer)
    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)
    
    event_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="events")
    participants = relationship("Participant", back_populates="event", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="event", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="event", cascade="all, delete-orphan")
    marketing_posts = relationship("MarketingPost", back_populates="event", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="event", cascade="all, delete-orphan")
    analytics_reports = relationship("AnalyticsReport", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event {self.name}>"


class Participant(Base):
    """Participant model"""
    __tablename__ = "participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    organization = Column(String(255))
    role = Column(String(100))
    
    is_speaker = Column(Boolean, default=False)
    is_sponsor = Column(Boolean, default=False)
    
    tags = Column(ARRAY(String), default=list)
    participant_metadata = Column(JSON, default=dict)
    
    registered_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="participants")
    
    def __repr__(self):
        return f"<Participant {self.full_name}>"


class Schedule(Base):
    """Schedule model"""
    __tablename__ = "schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    session_name = Column(String(255), nullable=False)
    session_type = Column(String(100))
    description = Column(Text)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    
    room = Column(String(100))
    speaker = Column(String(255))
    
    max_capacity = Column(Integer)
    tags = Column(ARRAY(String), default=list)
    
    schedule_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule {self.session_name}>"


class Email(Base):
    """Email model"""
    __tablename__ = "emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255))
    
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text)
    
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.PENDING, nullable=False)
    sent_at = Column(DateTime)
    
    error_message = Column(Text)
    email_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="emails")
    
    def __repr__(self):
        return f"<Email to {self.recipient_email}>"


class MarketingPost(Base):
    """Marketing post model"""
    __tablename__ = "marketing_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    platform = Column(String(50))
    post_type = Column(String(50))
    
    title = Column(String(500))
    content = Column(Text, nullable=False)
    
    hashtags = Column(ARRAY(String), default=list)
    scheduled_time = Column(DateTime)
    
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    
    engagement_metrics = Column(JSON, default=dict)
    marketing_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    event = relationship("Event", back_populates="marketing_posts")
    
    def __repr__(self):
        return f"<MarketingPost {self.platform}>"


class AgentLog(Base):
    """Agent execution log model"""
    __tablename__ = "agent_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"))
    
    agent_name = Column(String(100), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True))
    
    status = Column(String(50), nullable=False)
    
    inputs = Column(JSON, default=dict)
    outputs = Column(JSON, default=dict)
    
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    event = relationship("Event", back_populates="agent_logs")
    
    def __repr__(self):
        return f"<AgentLog {self.agent_name}>"


class AnalyticsReport(Base):
    """Analytics report model"""
    __tablename__ = "analytics_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    report_type = Column(String(100), nullable=False)
    report_name = Column(String(255), nullable=False)
    
    metrics = Column(JSON, default=dict)
    insights = Column(JSON, default=dict)
    recommendations = Column(JSON, default=dict)
    
    data_points = Column(Integer, default=0)
    confidence_score = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    event = relationship("Event", back_populates="analytics_reports")
    
    def __repr__(self):
        return f"<AnalyticsReport {self.report_name}>"