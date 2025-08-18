"""
Project model for storing project information.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    """Project model for storing project information."""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    token_symbol = Column(String(20), nullable=True, index=True)
    category = Column(Text, nullable=True, index=True)
    score = Column(Numeric(10, 2), nullable=True, index=True)
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    funding_rounds = relationship("FundingRound", back_populates="project", cascade="all, delete-orphan")
    investor_portfolios = relationship("InvestorPortfolio", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', slug='{self.slug}')>"