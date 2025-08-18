"""Webhook service for triggering webhook deliveries."""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.tasks.webhook_tasks import schedule_webhook_delivery
from app.models.webhook_delivery import WebhookDelivery

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for managing webhook deliveries."""
    
    @staticmethod
    def trigger_webhook_event(event_type: str, event_data: Dict[str, Any], 
                            webhook_configs: List[Dict[str, Any]] = None,
                            db: Session = None) -> List[str]:
        """Trigger webhook deliveries for an event.
        
        Args:
            event_type: Type of event that occurred
            event_data: Data associated with the event
            webhook_configs: List of webhook configurations to deliver to
            db: Database session (optional, will create if not provided)
            
        Returns:
            List of delivery IDs that were scheduled
        """
        if db is None:
            db = next(get_db())
            close_db = True
        else:
            close_db = False
        
        try:
            delivery_ids = []
            
            # If no webhook configs provided, get from database
            if webhook_configs is None:
                webhook_configs = WebhookService._get_webhook_configs_for_event(
                    event_type, db
                )
            
            for config in webhook_configs:
                try:
                    delivery_id = schedule_webhook_delivery.delay(
                        webhook_id=config.get('id'),
                        event_type=event_type,
                        event_data=event_data,
                        url=config.get('url'),
                        secret=config.get('secret'),
                        headers=config.get('headers', {})
                    )
                    
                    delivery_ids.append(delivery_id)
                    logger.info(f"Scheduled webhook delivery for event {event_type} to {config.get('url')}")
                    
                except Exception as e:
                    logger.error(f"Failed to schedule webhook delivery for {config.get('url')}: {str(e)}")
            
            return delivery_ids
            
        except Exception as e:
            logger.error(f"Failed to trigger webhook event {event_type}: {str(e)}")
            raise
        
        finally:
            if close_db:
                db.close()
    
    @staticmethod
    def _get_webhook_configs_for_event(event_type: str, db: Session) -> List[Dict[str, Any]]:
        """Get webhook configurations that should receive this event type.
        
        This is a placeholder implementation. In a real application, you would
        query your webhook configuration table to find webhooks that are
        subscribed to this event type.
        
        Args:
            event_type: The event type to find webhooks for
            db: Database session
            
        Returns:
            List of webhook configuration dictionaries
        """
        # TODO: Implement actual webhook configuration lookup
        # This would typically query a 'webhooks' table to find active webhooks
        # that are subscribed to the given event_type
        
        # Example implementation:
        # webhooks = db.query(Webhook).filter(
        #     Webhook.is_active == True,
        #     Webhook.events.contains([event_type])
        # ).all()
        # 
        # return [
        #     {
        #         'id': webhook.id,
        #         'url': webhook.url,
        #         'secret': webhook.secret,
        #         'headers': webhook.headers or {},
        #         'events': webhook.events
        #     }
        #     for webhook in webhooks
        # ]
        
        logger.warning(f"No webhook configuration lookup implemented for event type: {event_type}")
        return []
    
    @staticmethod
    def get_delivery_status(delivery_id: UUID, db: Session = None) -> Optional[Dict[str, Any]]:
        """Get the status of a webhook delivery.
        
        Args:
            delivery_id: UUID of the delivery to check
            db: Database session (optional)
            
        Returns:
            Dictionary with delivery status information or None if not found
        """
        if db is None:
            db = next(get_db())
            close_db = True
        else:
            close_db = False
        
        try:
            delivery = db.query(WebhookDelivery).filter(
                WebhookDelivery.id == delivery_id
            ).first()
            
            if not delivery:
                return None
            
            return {
                'id': delivery.id,
                'status': delivery.status,
                'attempt_count': delivery.attempt_count,
                'max_attempts': delivery.max_attempts,
                'created_at': delivery.created_at,
                'last_attempted_at': delivery.last_attempted_at,
                'delivered_at': delivery.delivered_at,
                'next_retry_at': delivery.next_retry_at,
                'last_error_message': delivery.last_error_message,
                'last_response_status': delivery.last_response_status
            }
            
        finally:
            if close_db:
                db.close()


# Convenience functions for common webhook events
def trigger_user_created_webhook(user_data: Dict[str, Any], db: Session = None) -> List[str]:
    """Trigger webhooks for user creation event."""
    return WebhookService.trigger_webhook_event(
        event_type="user.created",
        event_data=user_data,
        db=db
    )


def trigger_project_updated_webhook(project_data: Dict[str, Any], db: Session = None) -> List[str]:
    """Trigger webhooks for project update event."""
    return WebhookService.trigger_webhook_event(
        event_type="project.updated",
        event_data=project_data,
        db=db
    )


def trigger_funding_round_created_webhook(funding_data: Dict[str, Any], db: Session = None) -> List[str]:
    """Trigger webhooks for funding round creation event."""
    return WebhookService.trigger_webhook_event(
        event_type="funding_round.created",
        event_data=funding_data,
        db=db
    )


def trigger_investment_made_webhook(investment_data: Dict[str, Any], db: Session = None) -> List[str]:
    """Trigger webhooks for investment event."""
    return WebhookService.trigger_webhook_event(
        event_type="investment.made",
        event_data=investment_data,
        db=db
    )


def trigger_alert_created_webhook(alert_data: Dict[str, Any], db: Session = None) -> List[str]:
    """Trigger webhooks for alert creation event."""
    return WebhookService.trigger_webhook_event(
        event_type="alert.created",
        event_data=alert_data,
        db=db
    )