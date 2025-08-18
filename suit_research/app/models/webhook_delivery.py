"""Webhook delivery model for tracking webhook delivery status and attempts."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class WebhookDeliveryStatus(str, Enum):
    """Webhook delivery status enumeration."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class WebhookDelivery(Base):
    """Model for tracking webhook delivery attempts and status."""
    
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Webhook configuration reference
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id"), nullable=False)
    
    # Event information
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=False)
    
    # Delivery details
    url = Column(String(2048), nullable=False)
    http_method = Column(String(10), default="POST")
    headers = Column(JSON, default=dict)
    payload = Column(Text, nullable=False)
    signature = Column(String(256), nullable=False)  # HMAC-SHA256 signature
    
    # Status tracking
    status = Column(String(20), default=WebhookDeliveryStatus.PENDING)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    
    # Response tracking
    last_response_status = Column(Integer, nullable=True)
    last_response_body = Column(Text, nullable=True)
    last_response_headers = Column(JSON, nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    last_attempted_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
    
    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, status={self.status}, attempts={self.attempt_count})>"
    
    @property
    def is_deliverable(self) -> bool:
        """Check if the webhook delivery can be attempted."""
        return (
            self.status in [WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.RETRYING]
            and self.attempt_count < self.max_attempts
        )
    
    @property
    def should_retry(self) -> bool:
        """Check if the webhook delivery should be retried."""
        return (
            self.status == WebhookDeliveryStatus.FAILED
            and self.attempt_count < self.max_attempts
        )
    
    def calculate_next_retry_delay(self) -> int:
        """Calculate the next retry delay in seconds using exponential backoff."""
        # Base delay of 60 seconds, exponentially increasing
        base_delay = 60
        max_delay = 3600  # 1 hour maximum
        
        delay = min(base_delay * (2 ** self.attempt_count), max_delay)
        return delay
    
    def mark_as_delivered(self, response_status: int, response_body: str = None, response_headers: Dict = None):
        """Mark the delivery as successful."""
        self.status = WebhookDeliveryStatus.DELIVERED
        self.delivered_at = datetime.utcnow()
        self.last_response_status = response_status
        self.last_response_body = response_body
        self.last_response_headers = response_headers or {}
        self.last_error_message = None
    
    def mark_as_failed(self, error_message: str, response_status: int = None, response_body: str = None):
        """Mark the delivery as failed."""
        self.status = WebhookDeliveryStatus.FAILED
        self.last_attempted_at = datetime.utcnow()
        self.last_error_message = error_message
        self.last_response_status = response_status
        self.last_response_body = response_body
        
        # Schedule retry if attempts remaining
        if self.should_retry:
            self.status = WebhookDeliveryStatus.RETRYING
            retry_delay = self.calculate_next_retry_delay()
            self.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
    
    def increment_attempt(self):
        """Increment the attempt counter."""
        self.attempt_count += 1
        self.last_attempted_at = datetime.utcnow()


class WebhookDeliveryLog(Base):
    """Model for logging individual webhook delivery attempts."""
    
    __tablename__ = "webhook_delivery_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id = Column(UUID(as_uuid=True), ForeignKey("webhook_deliveries.id"), nullable=False)
    
    # Attempt details
    attempt_number = Column(Integer, nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow)
    
    # Request details
    request_headers = Column(JSON, default=dict)
    request_payload = Column(Text, nullable=False)
    
    # Response details
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Relationships
    delivery = relationship("WebhookDelivery", backref="logs")
    
    def __repr__(self):
        return f"<WebhookDeliveryLog(id={self.id}, attempt={self.attempt_number}, status={self.response_status})>"