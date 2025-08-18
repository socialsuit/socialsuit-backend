"""Celery tasks for webhook delivery with HMAC-SHA256 signing and retry mechanisms."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx
from celery import Celery
from celery.exceptions import Retry
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models.webhook_delivery import WebhookDelivery, WebhookDeliveryStatus, WebhookDeliveryLog
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_webhook_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for webhook payload.
    
    Args:
        payload: The webhook payload as a string
        secret: The webhook secret key
        
    Returns:
        The HMAC-SHA256 signature as a hex string
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


@celery_app.task(bind=True, max_retries=5)
def deliver_webhook(self, delivery_id: str, webhook_secret: str = None):
    """Deliver a webhook with HMAC-SHA256 signing and retry logic.
    
    Args:
        delivery_id: UUID of the webhook delivery record
        webhook_secret: Secret key for HMAC signing (optional)
    """
    db = next(get_db())
    
    try:
        # Get the delivery record
        delivery = db.query(WebhookDelivery).filter(
            WebhookDelivery.id == delivery_id
        ).first()
        
        if not delivery:
            logger.error(f"Webhook delivery {delivery_id} not found")
            return
        
        if not delivery.is_deliverable:
            logger.info(f"Webhook delivery {delivery_id} is not deliverable (status: {delivery.status}, attempts: {delivery.attempt_count})")
            return
        
        # Increment attempt counter
        delivery.increment_attempt()
        
        # Generate signature if secret is provided
        signature = None
        if webhook_secret:
            signature = generate_webhook_signature(delivery.payload, webhook_secret)
            delivery.signature = signature
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"SocialSuit-Webhook/1.0",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": str(delivery.id),
            "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp())),
        }
        
        if signature:
            headers["X-Webhook-Signature-256"] = signature
        
        # Add custom headers from delivery configuration
        if delivery.headers:
            headers.update(delivery.headers)
        
        # Create delivery log entry
        log_entry = WebhookDeliveryLog(
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count,
            request_headers=headers,
            request_payload=delivery.payload
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Make the HTTP request
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=delivery.http_method,
                    url=delivery.url,
                    headers=headers,
                    content=delivery.payload
                )
            
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log the response
            log_entry.response_status = response.status_code
            log_entry.response_headers = dict(response.headers)
            log_entry.response_body = response.text[:10000]  # Limit response body size
            log_entry.response_time_ms = response_time_ms
            
            # Check if delivery was successful
            if 200 <= response.status_code < 300:
                delivery.mark_as_delivered(
                    response_status=response.status_code,
                    response_body=response.text[:1000],
                    response_headers=dict(response.headers)
                )
                logger.info(f"Webhook delivery {delivery_id} successful (status: {response.status_code})")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                log_entry.error_message = error_msg
                delivery.mark_as_failed(
                    error_message=error_msg,
                    response_status=response.status_code,
                    response_body=response.text[:1000]
                )
                
                # Retry if attempts remaining
                if delivery.should_retry:
                    retry_delay = delivery.calculate_next_retry_delay()
                    logger.warning(f"Webhook delivery {delivery_id} failed, retrying in {retry_delay}s (attempt {delivery.attempt_count}/{delivery.max_attempts})")
                    raise self.retry(countdown=retry_delay)
                else:
                    logger.error(f"Webhook delivery {delivery_id} failed permanently after {delivery.attempt_count} attempts")
        
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            log_entry.error_message = error_msg
            log_entry.error_type = type(e).__name__
            
            delivery.mark_as_failed(error_message=error_msg)
            
            # Retry if attempts remaining
            if delivery.should_retry:
                retry_delay = delivery.calculate_next_retry_delay()
                logger.warning(f"Webhook delivery {delivery_id} failed with request error, retrying in {retry_delay}s (attempt {delivery.attempt_count}/{delivery.max_attempts})")
                raise self.retry(countdown=retry_delay)
            else:
                logger.error(f"Webhook delivery {delivery_id} failed permanently with request error after {delivery.attempt_count} attempts")
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            log_entry.error_message = error_msg
            log_entry.error_type = type(e).__name__
            
            delivery.mark_as_failed(error_message=error_msg)
            
            # Retry if attempts remaining
            if delivery.should_retry:
                retry_delay = delivery.calculate_next_retry_delay()
                logger.warning(f"Webhook delivery {delivery_id} failed with unexpected error, retrying in {retry_delay}s (attempt {delivery.attempt_count}/{delivery.max_attempts})")
                raise self.retry(countdown=retry_delay)
            else:
                logger.error(f"Webhook delivery {delivery_id} failed permanently with unexpected error after {delivery.attempt_count} attempts")
        
        finally:
            # Save the log entry
            db.add(log_entry)
            db.commit()
    
    except Exception as e:
        logger.error(f"Critical error in webhook delivery task {delivery_id}: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


@celery_app.task
def schedule_webhook_delivery(webhook_id: str, event_type: str, event_data: Dict[str, Any], 
                            url: str, secret: str = None, headers: Dict[str, str] = None,
                            delay_seconds: int = 0):
    """Schedule a webhook delivery.
    
    Args:
        webhook_id: UUID of the webhook configuration
        event_type: Type of event that triggered the webhook
        event_data: Event data to be sent in the payload
        url: Webhook URL to deliver to
        secret: Secret key for HMAC signing (optional)
        headers: Additional headers to include (optional)
        delay_seconds: Delay before delivery in seconds (optional)
    """
    db = next(get_db())
    
    try:
        # Create the payload
        payload_data = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data
        }
        payload = json.dumps(payload_data, separators=(',', ':'))
        
        # Generate signature if secret provided
        signature = ""
        if secret:
            signature = generate_webhook_signature(payload, secret)
        
        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            event_data=event_data,
            url=url,
            payload=payload,
            signature=signature,
            headers=headers or {},
            scheduled_at=datetime.utcnow() + timedelta(seconds=delay_seconds)
        )
        
        db.add(delivery)
        db.commit()
        
        # Schedule the delivery task
        if delay_seconds > 0:
            deliver_webhook.apply_async(
                args=[str(delivery.id), secret],
                countdown=delay_seconds
            )
        else:
            deliver_webhook.delay(str(delivery.id), secret)
        
        logger.info(f"Scheduled webhook delivery {delivery.id} for event {event_type}")
        return str(delivery.id)
    
    except Exception as e:
        logger.error(f"Failed to schedule webhook delivery: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()


@celery_app.task
def retry_failed_webhooks():
    """Periodic task to retry failed webhook deliveries."""
    db = next(get_db())
    
    try:
        # Find deliveries that are ready for retry
        now = datetime.utcnow()
        failed_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.status == WebhookDeliveryStatus.RETRYING,
            WebhookDelivery.next_retry_at <= now,
            WebhookDelivery.attempt_count < WebhookDelivery.max_attempts
        ).all()
        
        for delivery in failed_deliveries:
            # Get the webhook secret (this would need to be retrieved from webhook config)
            webhook_secret = None  # TODO: Retrieve from webhook configuration
            
            # Schedule retry
            deliver_webhook.delay(str(delivery.id), webhook_secret)
            logger.info(f"Scheduled retry for webhook delivery {delivery.id}")
        
        logger.info(f"Scheduled {len(failed_deliveries)} webhook delivery retries")
        return len(failed_deliveries)
    
    except Exception as e:
        logger.error(f"Failed to retry failed webhooks: {str(e)}")
        raise
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_webhook_logs(days_to_keep: int = 30):
    """Clean up old webhook delivery logs.
    
    Args:
        days_to_keep: Number of days to keep logs (default: 30)
    """
    db = next(get_db())
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old delivery logs
        deleted_logs = db.query(WebhookDeliveryLog).filter(
            WebhookDeliveryLog.attempted_at < cutoff_date
        ).delete()
        
        # Delete old completed deliveries
        deleted_deliveries = db.query(WebhookDelivery).filter(
            WebhookDelivery.status == WebhookDeliveryStatus.DELIVERED,
            WebhookDelivery.delivered_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_logs} webhook logs and {deleted_deliveries} deliveries older than {days_to_keep} days")
        return {"deleted_logs": deleted_logs, "deleted_deliveries": deleted_deliveries}
    
    except Exception as e:
        logger.error(f"Failed to cleanup old webhook logs: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()