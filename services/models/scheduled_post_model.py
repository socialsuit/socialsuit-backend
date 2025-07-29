from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
from services.database.database import Base
import enum

class PostStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    retry = "retry"

class ScheduledPost(Base):
    __tablename__= "scheduled_posts" 

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(String, ForeignKey("users.id"))  # link to user_model
    platform = Column(String)  # e.g. facebook, instagram
    
    post_payload = Column(JSON)  # e.g. {"caption": "...", "image_url": "..."}
    
    scheduled_time = Column(DateTime)  # e.g. 2025-06-24T05:00:00Z
    
    status = Column(Enum(PostStatus), default=PostStatus.pending)
    retries = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())