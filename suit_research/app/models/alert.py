"""
Alert and watchlist models for user notifications and tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Numeric, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    """Alert model for user notifications based on project changes."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # funding, score_change, news, etc.
    threshold = Column(JSON, nullable=True)  # Threshold conditions for triggering alert
    is_active = Column(String(10), default="true")  # active, inactive
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, user_id={self.user_id}, project_id={self.project_id}, type='{self.alert_type}')>"


class Watchlist(Base):
    """Watchlist model for users to track projects."""
    
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    notes = Column(String(1000), nullable=True)  # User notes about the project
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="watchlists")
    
    # Unique constraint on user_id + project_id
    __table_args__ = (
        {"extend_existing": True}
    )
    
    def __repr__(self):
        return f"<Watchlist(id={self.id}, user_id={self.user_id}, project_id={self.project_id})>"


class Notification(Base):
    """Notification model for storing triggered alerts."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    message = Column(String(1000), nullable=False)
    notification_type = Column(String(50), nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    alert = relationship("Alert")
    project = relationship("Project")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, alert_id={self.alert_id}, is_read={self.is_read})>"