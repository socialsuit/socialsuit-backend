"""Admin endpoints for webhook management and re-delivery."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.auth_middleware import require_admin
from app.models.webhook_delivery import WebhookDelivery, WebhookDeliveryStatus, WebhookDeliveryLog
from app.tasks.webhook_tasks import deliver_webhook
from app.api.schemas.webhook_admin import (
    WebhookDeliveryResponse,
    WebhookDeliveryLogResponse,
    WebhookDeliveryListResponse,
    ResendWebhookRequest,
    ResendWebhookResponse
)

router = APIRouter()


@router.get("/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    status: Optional[WebhookDeliveryStatus] = Query(None, description="Filter by delivery status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    webhook_id: Optional[UUID] = Query(None, description="Filter by webhook ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of deliveries to return"),
    offset: int = Query(0, ge=0, description="Number of deliveries to skip"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """List webhook deliveries with optional filtering."""
    
    query = db.query(WebhookDelivery)
    
    # Apply filters
    if status:
        query = query.filter(WebhookDelivery.status == status)
    if event_type:
        query = query.filter(WebhookDelivery.event_type == event_type)
    if webhook_id:
        query = query.filter(WebhookDelivery.webhook_id == webhook_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    deliveries = query.order_by(desc(WebhookDelivery.created_at)).offset(offset).limit(limit).all()
    
    return WebhookDeliveryListResponse(
        deliveries=[WebhookDeliveryResponse.from_orm(d) for d in deliveries],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery(
    delivery_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Get details of a specific webhook delivery."""
    
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.id == delivery_id
    ).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Webhook delivery not found")
    
    return WebhookDeliveryResponse.from_orm(delivery)


@router.get("/deliveries/{delivery_id}/logs", response_model=List[WebhookDeliveryLogResponse])
async def get_webhook_delivery_logs(
    delivery_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Get delivery attempt logs for a specific webhook delivery."""
    
    # Verify delivery exists
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.id == delivery_id
    ).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Webhook delivery not found")
    
    # Get logs
    logs = db.query(WebhookDeliveryLog).filter(
        WebhookDeliveryLog.delivery_id == delivery_id
    ).order_by(WebhookDeliveryLog.attempted_at).all()
    
    return [WebhookDeliveryLogResponse.from_orm(log) for log in logs]


@router.post("/deliveries/{delivery_id}/resend", response_model=ResendWebhookResponse)
async def resend_webhook_delivery(
    delivery_id: UUID,
    request: ResendWebhookRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Re-send a failed webhook delivery."""
    
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.id == delivery_id
    ).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Webhook delivery not found")
    
    # Check if delivery can be resent
    if delivery.status == WebhookDeliveryStatus.DELIVERED and not request.force:
        raise HTTPException(
            status_code=400, 
            detail="Delivery already succeeded. Use force=true to resend anyway."
        )
    
    # Reset delivery status for retry
    if request.reset_attempts:
        delivery.attempt_count = 0
        delivery.status = WebhookDeliveryStatus.PENDING
        delivery.last_error_message = None
        delivery.next_retry_at = None
    elif delivery.status == WebhookDeliveryStatus.FAILED:
        delivery.status = WebhookDeliveryStatus.RETRYING
    
    # Update max attempts if provided
    if request.max_attempts is not None:
        delivery.max_attempts = request.max_attempts
    
    db.commit()
    
    # Schedule the delivery
    webhook_secret = request.webhook_secret  # Use provided secret or get from webhook config
    task = deliver_webhook.delay(str(delivery.id), webhook_secret)
    
    return ResendWebhookResponse(
        delivery_id=delivery.id,
        task_id=task.id,
        message="Webhook delivery has been scheduled for resend",
        scheduled_at=datetime.utcnow()
    )


@router.post("/deliveries/resend-failed", response_model=dict)
async def resend_all_failed_deliveries(
    webhook_id: Optional[UUID] = Query(None, description="Filter by webhook ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age of failed deliveries in hours"),
    reset_attempts: bool = Query(False, description="Reset attempt counter"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Re-send all failed webhook deliveries matching the criteria."""
    
    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    # Build query for failed deliveries
    query = db.query(WebhookDelivery).filter(
        WebhookDelivery.status == WebhookDeliveryStatus.FAILED,
        WebhookDelivery.created_at >= cutoff_time
    )
    
    if webhook_id:
        query = query.filter(WebhookDelivery.webhook_id == webhook_id)
    if event_type:
        query = query.filter(WebhookDelivery.event_type == event_type)
    
    failed_deliveries = query.all()
    
    scheduled_count = 0
    for delivery in failed_deliveries:
        # Reset delivery status if requested
        if reset_attempts:
            delivery.attempt_count = 0
            delivery.last_error_message = None
            delivery.next_retry_at = None
        
        delivery.status = WebhookDeliveryStatus.RETRYING
        
        # Schedule the delivery (webhook secret would need to be retrieved from config)
        deliver_webhook.delay(str(delivery.id), None)  # TODO: Get webhook secret
        scheduled_count += 1
    
    db.commit()
    
    return {
        "message": f"Scheduled {scheduled_count} failed webhook deliveries for resend",
        "scheduled_count": scheduled_count,
        "total_failed": len(failed_deliveries)
    }


@router.delete("/deliveries/{delivery_id}")
async def cancel_webhook_delivery(
    delivery_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Cancel a pending or retrying webhook delivery."""
    
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.id == delivery_id
    ).first()
    
    if not delivery:
        raise HTTPException(status_code=404, detail="Webhook delivery not found")
    
    if delivery.status not in [WebhookDeliveryStatus.PENDING, WebhookDeliveryStatus.RETRYING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel delivery with status: {delivery.status}"
        )
    
    delivery.status = WebhookDeliveryStatus.CANCELLED
    db.commit()
    
    return {"message": "Webhook delivery cancelled successfully"}


@router.get("/stats")
async def get_webhook_delivery_stats(
    webhook_id: Optional[UUID] = Query(None, description="Filter by webhook ID"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin)
):
    """Get webhook delivery statistics."""
    
    from sqlalchemy import func
    from datetime import timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(WebhookDelivery).filter(
        WebhookDelivery.created_at >= cutoff_time
    )
    
    if webhook_id:
        query = query.filter(WebhookDelivery.webhook_id == webhook_id)
    
    # Get status counts
    status_counts = db.query(
        WebhookDelivery.status,
        func.count(WebhookDelivery.id)
    ).filter(
        WebhookDelivery.created_at >= cutoff_time
    )
    
    if webhook_id:
        status_counts = status_counts.filter(WebhookDelivery.webhook_id == webhook_id)
    
    status_counts = status_counts.group_by(WebhookDelivery.status).all()
    
    # Get average response time for successful deliveries
    avg_response_time = db.query(
        func.avg(WebhookDeliveryLog.response_time_ms)
    ).join(WebhookDelivery).filter(
        WebhookDelivery.created_at >= cutoff_time,
        WebhookDeliveryLog.response_status.between(200, 299)
    )
    
    if webhook_id:
        avg_response_time = avg_response_time.filter(WebhookDelivery.webhook_id == webhook_id)
    
    avg_response_time = avg_response_time.scalar() or 0
    
    return {
        "time_window_hours": hours,
        "webhook_id": webhook_id,
        "status_counts": {status: count for status, count in status_counts},
        "average_response_time_ms": round(avg_response_time, 2),
        "total_deliveries": sum(count for _, count in status_counts)
    }