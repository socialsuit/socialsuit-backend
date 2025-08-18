"""
API management models for API keys and webhooks.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ApiKey(Base):
    """API key model for authentication and access control."""
    
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    scopes = Column(JSON, nullable=True)  # Array of allowed scopes/permissions
    name = Column(String(255), nullable=True)  # Optional name for the API key
    description = Column(Text, nullable=True)  # Optional description
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', revoked={'Yes' if self.revoked_at else 'No'})>"


class Webhook(Base):
    """Webhook model for event notifications."""
    
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), nullable=False)
    secret = Column(String(255), nullable=True)  # For webhook signature verification
    events = Column(JSON, nullable=False)  # Array of event types to listen for
    name = Column(String(255), nullable=True)  # Optional name for the webhook
    description = Column(Text, nullable=True)  # Optional description
    is_active = Column(String(10), default="true")  # active, inactive
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, url='{self.url}', active={self.is_active})>"