"""
Celery tasks for notifications.
"""

from celery import current_task
from app.core.celery_app import celery_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_email_notification(self, to_email: str, subject: str, body: str):
    """
    Send email notification.
    """
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'Sending email', 'to': to_email}
        )
        
        # In production, implement actual email sending
        # For now, just log the email
        logger.info(f"Email sent to {to_email}: {subject}")
        
        return {
            'status': 'sent',
            'to_email': to_email,
            'subject': subject,
            'sent_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'to_email': to_email}
        )
        raise exc


@celery_app.task
def send_webhook_notification(webhook_url: str, payload: dict):
    """
    Send webhook notification.
    """
    import aiohttp
    import asyncio
    
    async def send_webhook():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json=payload) as response:
                    return {
                        'status': 'sent',
                        'webhook_url': webhook_url,
                        'response_status': response.status,
                        'sent_at': datetime.utcnow().isoformat()
                    }
            except Exception as e:
                return {
                    'status': 'failed',
                    'webhook_url': webhook_url,
                    'error': str(e),
                    'failed_at': datetime.utcnow().isoformat()
                }
    
    return asyncio.run(send_webhook())


@celery_app.task
def send_slack_notification(channel: str, message: str):
    """
    Send Slack notification.
    """
    # In production, implement actual Slack integration
    logger.info(f"Slack message to {channel}: {message}")
    
    return {
        'status': 'sent',
        'channel': channel,
        'message': message,
        'sent_at': datetime.utcnow().isoformat()
    }