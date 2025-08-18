"""
Investor model for storing investor information and portfolio relationships.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Investor(Base):
    """Investor model for storing investor information."""
    
    __tablename__ = "investors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    website = Column(String(500), nullable=True)
    profile = Column(JSON, nullable=True)  # Additional investor profile data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    portfolios = relationship("InvestorPortfolio", back_populates="investor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Investor(id={self.id}, name='{self.name}', slug='{self.slug}')>"


class InvestorPortfolio(Base):
    """Junction table for investor-project relationships."""
    
    __tablename__ = "investors_portfolio"
    
    investor_id = Column(Integer, ForeignKey("investors.id"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    first_invested_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    investor = relationship("Investor", back_populates="portfolios")
    project = relationship("Project", back_populates="investor_portfolios")
    
    def __repr__(self):
        return f"<InvestorPortfolio(investor_id={self.investor_id}, project_id={self.project_id})>"