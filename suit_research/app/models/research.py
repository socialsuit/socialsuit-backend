"""
Research model for storing research data.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Research(Base):
    """Research model."""
    
    __tablename__ = "research"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    source_url = Column(String(1000), nullable=True)
    status = Column(String(50), default="draft", index=True)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    # owner = relationship("User", back_populates="research_items")
    
    def __repr__(self):
        return f"<Research(id={self.id}, title='{self.title}', status='{self.status}')>"


class ResearchCategory(Base):
    """Research category model."""
    
    __tablename__ = "research_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ResearchCategory(id={self.id}, name='{self.name}')>"