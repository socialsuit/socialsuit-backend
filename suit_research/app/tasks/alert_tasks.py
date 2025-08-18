"""Background tasks for processing alerts and notifications."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.alert import Alert, Notification, Watchlist
from app.models.project import Project
from app.models.funding import FundingRound
from app.models.user import User
from app.tasks.notification_tasks import send_webhook_notification, send_email_notification

logger = logging.getLogger(__name__)


class AlertProcessor:
    """Processes alerts and triggers notifications."""
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
    
    async def process_funding_alerts(self) -> int:
        """Process funding received alerts."""
        processed_count = 0
        
        try:
            # Get recent funding rounds (last 24 hours)
            since_time = datetime.utcnow() - timedelta(hours=24)
            
            funding_query = (
                select(FundingRound)
                .where(FundingRound.created_at >= since_time)
                .options(selectinload(FundingRound.project))
            )
            
            funding_result = await self.session.execute(funding_query)
            recent_funding_rounds = funding_result.scalars().all()
            
            for funding_round in recent_funding_rounds:
                # Find alerts for this project
                alert_query = (
                    select(Alert)
                    .where(
                        and_(
                            Alert.project_id == funding_round.project_id,
                            Alert.alert_type == "funding_received",
                            Alert.is_active == "active",
                            or_(
                                Alert.last_triggered_at.is_(None),
                                Alert.last_triggered_at < since_time
                            )
                        )
                    )
                    .options(selectinload(Alert.user), selectinload(Alert.project))
                )
                
                alert_result = await self.session.execute(alert_query)
                alerts = alert_result.scalars().all()
                
                for alert in alerts:
                    await self._trigger_alert(alert, funding_round)
                    processed_count += 1
            
            await self.session.commit()
            logger.info(f"Processed {processed_count} funding alerts")
            
        except Exception as e:
            logger.error(f"Error processing funding alerts: {e}")
            await self.session.rollback()
            raise
        
        return processed_count
    
    async def process_listing_alerts(self) -> int:
        """Process listing alerts."""
        processed_count = 0
        
        try:
            # Get projects that were recently listed (mock implementation)
            # In a real implementation, this would check for actual listing events
            since_time = datetime.utcnow() - timedelta(hours=24)
            
            # For demo purposes, we'll check for projects with recent token_symbol updates
            project_query = (
                select(Project)
                .where(
                    and_(
                        Project.token_symbol.isnot(None),
                        Project.updated_at >= since_time
                    )
                )
            )
            
            project_result = await self.session.execute(project_query)
            recently_listed_projects = project_result.scalars().all()
            
            for project in recently_listed_projects:
                # Find listing alerts for this project
                alert_query = (
                    select(Alert)
                    .where(
                        and_(
                            Alert.project_id == project.id,
                            Alert.alert_type == "listing",
                            Alert.is_active == "active",
                            or_(
                                Alert.last_triggered_at.is_(None),
                                Alert.last_triggered_at < since_time
                            )
                        )
                    )
                    .options(selectinload(Alert.user), selectinload(Alert.project))
                )
                
                alert_result = await self.session.execute(alert_query)
                alerts = alert_result.scalars().all()
                
                for alert in alerts:
                    await self._trigger_alert(alert, project)
                    processed_count += 1
            
            await self.session.commit()
            logger.info(f"Processed {processed_count} listing alerts")
            
        except Exception as e:
            logger.error(f"Error processing listing alerts: {e}")
            await self.session.rollback()
            raise
        
        return processed_count
    
    async def process_score_change_alerts(self) -> int:
        """Process score change alerts."""
        processed_count = 0
        
        try:
            # Get projects with recent score changes
            since_time = datetime.utcnow() - timedelta(hours=24)
            
            project_query = (
                select(Project)
                .where(
                    and_(
                        Project.score.isnot(None),
                        Project.updated_at >= since_time
                    )
                )
            )
            
            project_result = await self.session.execute(project_query)
            projects_with_score_changes = project_result.scalars().all()
            
            for project in projects_with_score_changes:
                # Find score change alerts for this project
                alert_query = (
                    select(Alert)
                    .where(
                        and_(
                            Alert.project_id == project.id,
                            Alert.alert_type == "score_change",
                            Alert.is_active == "active",
                            or_(
                                Alert.last_triggered_at.is_(None),
                                Alert.last_triggered_at < since_time
                            )
                        )
                    )
                    .options(selectinload(Alert.user), selectinload(Alert.project))
                )
                
                alert_result = await self.session.execute(alert_query)
                alerts = alert_result.scalars().all()
                
                for alert in alerts:
                    # Check if score change meets threshold
                    if await self._check_score_threshold(alert, project):
                        await self._trigger_alert(alert, project)
                        processed_count += 1
            
            await self.session.commit()
            logger.info(f"Processed {processed_count} score change alerts")
            
        except Exception as e:
            logger.error(f"Error processing score change alerts: {e}")
            await self.session.rollback()
            raise
        
        return processed_count
    
    async def _check_score_threshold(self, alert: Alert, project: Project) -> bool:
        """Check if score change meets the alert threshold."""
        if not alert.threshold or not project.score:
            return True  # Trigger if no threshold specified
        
        threshold_config = alert.threshold
        min_change = threshold_config.get('min_change', 0.1)
        direction = threshold_config.get('direction', 'any')  # 'increase', 'decrease', 'any'
        
        # For demo purposes, assume any score change triggers the alert
        # In a real implementation, you'd compare with previous score values
        return True
    
    async def _trigger_alert(self, alert: Alert, event_data: Any) -> None:
        """Trigger an alert and create notification."""
        try:
            # Create notification message
            message = await self._create_notification_message(alert, event_data)
            
            # Create notification record
            notification = Notification(
                user_id=alert.user_id,
                alert_id=alert.id,
                project_id=alert.project_id,
                message=message,
                notification_type=alert.alert_type,
                is_read=False
            )
            
            self.session.add(notification)
            
            # Update alert's last triggered time
            alert.last_triggered_at = datetime.utcnow()
            
            # Send webhook notification if configured
            await self._send_webhook_notification(alert, notification)
            
            # Send email notification if configured
            await self._send_email_notification(alert, notification)
            
            logger.info(f"Alert {alert.id} triggered for user {alert.user_id}")
            
        except Exception as e:
            logger.error(f"Error triggering alert {alert.id}: {e}")
            raise
    
    async def _create_notification_message(self, alert: Alert, event_data: Any) -> str:
        """Create notification message based on alert type and event data."""
        project_name = alert.project.name if alert.project else "Unknown Project"
        
        if alert.alert_type == "funding_received":
            if hasattr(event_data, 'amount_usd') and event_data.amount_usd:
                return f"🚀 {project_name} received ${event_data.amount_usd:,.0f} in funding!"
            else:
                return f"🚀 {project_name} received new funding!"
        
        elif alert.alert_type == "listing":
            token_symbol = getattr(event_data, 'token_symbol', None)
            if token_symbol:
                return f"📈 {project_name} token ({token_symbol}) is now listed!"
            else:
                return f"📈 {project_name} is now listed!"
        
        elif alert.alert_type == "score_change":
            score = getattr(event_data, 'score', None)
            if score:
                return f"📊 {project_name} score updated to {score:.2f}"
            else:
                return f"📊 {project_name} score has been updated"
        
        elif alert.alert_type == "token_price_threshold":
            return f"💰 {project_name} token price threshold reached!"
        
        else:
            return f"🔔 Alert triggered for {project_name}"
    
    async def _send_webhook_notification(self, alert: Alert, notification: Notification) -> None:
        """Send webhook notification if configured."""
        try:
            # Check if user has webhook URL configured (mock implementation)
            webhook_url = getattr(alert.user, 'webhook_url', None)
            
            if webhook_url:
                webhook_data = {
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "project_id": alert.project_id,
                    "alert_type": alert.alert_type,
                    "message": notification.message,
                    "timestamp": notification.created_at.isoformat(),
                    "project_name": alert.project.name if alert.project else None
                }
                
                await send_webhook_notification(webhook_url, webhook_data)
                logger.info(f"Webhook sent for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Error sending webhook for alert {alert.id}: {e}")
    
    async def _send_email_notification(self, alert: Alert, notification: Notification) -> None:
        """Send email notification if configured."""
        try:
            # Check if user has email configured and wants email notifications
            user_email = getattr(alert.user, 'email', None)
            email_notifications_enabled = getattr(alert.user, 'email_notifications', False)
            
            if user_email and email_notifications_enabled:
                subject = f"Alert: {alert.project.name if alert.project else 'Project Update'}"
                
                await send_email_notification(
                    to_email=user_email,
                    subject=subject,
                    message=notification.message
                )
                logger.info(f"Email sent for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Error sending email for alert {alert.id}: {e}")


async def process_all_alerts() -> Dict[str, int]:
    """Process all types of alerts. This function should be called by a scheduler."""
    results = {
        "funding_alerts": 0,
        "listing_alerts": 0,
        "score_change_alerts": 0,
        "total_processed": 0
    }
    
    try:
        async with AlertProcessor() as processor:
            # Process different types of alerts
            results["funding_alerts"] = await processor.process_funding_alerts()
            results["listing_alerts"] = await processor.process_listing_alerts()
            results["score_change_alerts"] = await processor.process_score_change_alerts()
            
            results["total_processed"] = (
                results["funding_alerts"] + 
                results["listing_alerts"] + 
                results["score_change_alerts"]
            )
            
            logger.info(f"Alert processing completed: {results}")
    
    except Exception as e:
        logger.error(f"Error in alert processing: {e}")
        raise
    
    return results


async def simulate_funding_event(project_id: int, amount: float = 1000000.0) -> bool:
    """Simulate a funding event for testing purposes."""
    try:
        async with AlertProcessor() as processor:
            # Create a mock funding round
            from app.models.funding import FundingRound
            
            funding_round = FundingRound(
                project_id=project_id,
                round_type="Series A",
                amount_usd=amount,
                currency="USD",
                announced_at=datetime.utcnow()
            )
            
            processor.session.add(funding_round)
            await processor.session.commit()
            
            # Process funding alerts immediately
            processed_count = await processor.process_funding_alerts()
            
            logger.info(f"Simulated funding event for project {project_id}, triggered {processed_count} alerts")
            return processed_count > 0
    
    except Exception as e:
        logger.error(f"Error simulating funding event: {e}")
        return False


if __name__ == "__main__":
    # For testing purposes
    asyncio.run(process_all_alerts())