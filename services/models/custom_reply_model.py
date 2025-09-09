from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from services.database.database import Base

class CustomReply(Base):
    """Model for storing custom brand replies in PostgreSQL.
    
    This model allows brands to define their own custom replies for specific intents/keywords
    across different platforms.
    """
    __tablename__ = "custom_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(String(50), nullable=False, index=True)
    intent = Column(String(100), nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    custom_reply = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Create composite indexes for faster lookups
    __table_args__ = (
        Index('idx_brand_intent', 'brand_id', 'intent'),
        Index('idx_brand_keyword', 'brand_id', 'keyword'),
        Index('idx_brand_platform', 'brand_id', 'platform'),
    )
    
    def __repr__(self):
        return f"<CustomReply(id={self.id}, brand_id={self.brand_id}, intent={self.intent}, platform={self.platform})>"