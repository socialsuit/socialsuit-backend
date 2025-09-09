from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4

from sparkr.app.models.schemas import StatusEnum, PlatformEnum, VerificationStatusEnum


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid4())


class Campaign(SQLModel, table=True):
    """Campaign database model"""
    __tablename__ = "campaigns"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tasks: List["Task"] = Relationship(back_populates="campaign")


class Task(SQLModel, table=True):
    """Task database model"""
    __tablename__ = "tasks"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    campaign_id: str = Field(foreign_key="campaigns.id")
    title: str
    description: Optional[str] = None
    platform: PlatformEnum
    points: int = Field(ge=0)
    status: StatusEnum = Field(default=StatusEnum.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    campaign: Campaign = Relationship(back_populates="tasks")
    submissions: List["Submission"] = Relationship(back_populates="task")


class Submission(SQLModel, table=True):
    """Submission database model"""
    __tablename__ = "submissions"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    task_id: str = Field(foreign_key="tasks.id")
    user_id: str = Field(foreign_key="users.id")
    submission_url: str
    tweet_id: Optional[str] = None
    ig_post_id: Optional[str] = None
    proof_url: Optional[str] = None
    status: VerificationStatusEnum = Field(default=VerificationStatusEnum.PENDING)
    points_awarded: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: Task = Relationship(back_populates="submissions")
    user: "User" = Relationship(back_populates="submissions")


class User(SQLModel, table=True):
    """User database model"""
    __tablename__ = "users"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    total_points: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    submissions: List[Submission] = Relationship(back_populates="user")
    rewards: List["Reward"] = Relationship()