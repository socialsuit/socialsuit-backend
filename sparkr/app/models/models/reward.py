from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid4())


class Reward(SQLModel, table=True):
    """Reward database model for storing awarded points"""
    __tablename__ = "rewards"
    
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    submission_id: str = Field(foreign_key="submissions.id")
    points: int = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship()
    submission: "Submission" = Relationship()