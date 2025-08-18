"""
Funding round model for storing investment information.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class FundingRound(Base):
    """Funding round model for storing investment information."""
    
    __tablename__ = "funding_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    round_type = Column(String(50), nullable=False, index=True)  # seed, series_a, series_b, etc.
    amount_usd = Column(Numeric(20, 2), nullable=True, index=True)
    currency = Column(String(10), nullable=True)
    announced_at = Column(DateTime(timezone=True), nullable=True, index=True)
    investors = Column(JSON, nullable=True)  # Array of investor information
    source_url = Column(String(1000), nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="funding_rounds")
    
    def __repr__(self):
        return f"<FundingRound(id={self.id}, project_id={self.project_id}, round_type='{self.round_type}', amount_usd={self.amount_usd})>"