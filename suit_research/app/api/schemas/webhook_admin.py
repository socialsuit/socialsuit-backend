"""Pydantic schemas for webhook admin endpoints."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.webhook_delivery import WebhookDeliveryStatus


class WebhookDeliveryResponse(BaseModel):
    """Response schema for webhook delivery details."""
    
    id: UUID
    webhook_id: UUID
    event_type: str
    event_data: Dict[str, Any]
    url: str
    http_method: str = "POST"
    headers: Dict[str, str] = {}
    payload: str
    signature: str
    status: WebhookDeliveryStatus
    attempt_count: int
    max_attempts: int
    last_response_status: Optional[int] = None
    last_response_body: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    scheduled_at: datetime
    last_attempted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WebhookDeliveryLogResponse(BaseModel):
    """Response schema for webhook delivery log entries."""
    
    id: UUID
    delivery_id: UUID
    attempt_number: int
    attempted_at: datetime
    request_headers: Dict[str, str] = {}
    request_payload: str
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WebhookDeliveryListResponse(BaseModel):
    """Response schema for paginated webhook delivery list."""
    
    deliveries: List[WebhookDeliveryResponse]
    total: int
    limit: int
    offset: int
    
    @property
    def has_more(self) -> bool:
        """Check if there are more deliveries available."""
        return self.offset + self.limit < self.total


class ResendWebhookRequest(BaseModel):
    """Request schema for resending webhook deliveries."""
    
    force: bool = Field(
        default=False,
        description="Force resend even if delivery was successful"
    )
    reset_attempts: bool = Field(
        default=False,
        description="Reset the attempt counter to 0"
    )
    max_attempts: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Override the maximum number of attempts"
    )
    webhook_secret: Optional[str] = Field(
        default=None,
        description="Webhook secret for HMAC signing (if different from original)"
    )


class ResendWebhookResponse(BaseModel):
    """Response schema for webhook resend operation."""
    
    delivery_id: UUID
    task_id: str
    message: str
    scheduled_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookDeliveryStatsResponse(BaseModel):
    """Response schema for webhook delivery statistics."""
    
    time_window_hours: int
    webhook_id: Optional[UUID] = None
    status_counts: Dict[str, int]
    average_response_time_ms: float
    total_deliveries: int
    success_rate: Optional[float] = None
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calculate success rate
        delivered = self.status_counts.get(WebhookDeliveryStatus.DELIVERED, 0)
        if self.total_deliveries > 0:
            self.success_rate = round((delivered / self.total_deliveries) * 100, 2)


class BulkResendRequest(BaseModel):
    """Request schema for bulk resending failed webhooks."""
    
    webhook_id: Optional[UUID] = Field(
        default=None,
        description="Filter by specific webhook ID"
    )
    event_type: Optional[str] = Field(
        default=None,
        description="Filter by event type"
    )
    max_age_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Maximum age of failed deliveries in hours"
    )
    reset_attempts: bool = Field(
        default=False,
        description="Reset attempt counters for all deliveries"
    )


class BulkResendResponse(BaseModel):
    """Response schema for bulk resend operation."""
    
    message: str
    scheduled_count: int
    total_failed: int
    webhook_id: Optional[UUID] = None
    event_type: Optional[str] = None


class WebhookDeliveryFilter(BaseModel):
    """Filter schema for webhook delivery queries."""
    
    status: Optional[WebhookDeliveryStatus] = None
    event_type: Optional[str] = None
    webhook_id: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    url_contains: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }