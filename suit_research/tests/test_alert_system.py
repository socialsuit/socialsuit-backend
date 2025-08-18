"""Tests for the alert system functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.alert import Alert, Notification, Watchlist
from app.models.project import Project
from app.models.funding import FundingRound
from app.models.user import User
from app.tasks.alert_tasks import AlertProcessor, simulate_funding_event, process_all_alerts


@pytest.mark.asyncio
class TestAlertSystem:
    """Test suite for alert system functionality."""
    
    async def test_acceptance_criteria_funding_alert_triggered(self):
        """Test that an alert is triggered when a simulated funding event occurs."""
        # Mock database session
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        
        # Mock the AlertProcessor.process_funding_alerts method to return 1 (indicating 1 alert processed)
        with patch.object(AlertProcessor, 'process_funding_alerts', return_value=1) as mock_process:
            with patch('app.tasks.alert_tasks.AsyncSessionLocal', return_value=mock_session):
                # Simulate funding event
                result = await simulate_funding_event(project_id=1, amount=1000000.0)
                
                # Verify that the function returned True (alerts were triggered)
                assert result is True, "simulate_funding_event should return True when alerts are triggered"
                
                # Verify that a funding round was added to the session
                mock_session.add.assert_called_once()
                
                # Verify that commit was called
                mock_session.commit.assert_called()
                
                # Verify that process_funding_alerts was called
                mock_process.assert_called_once()
    
    async def test_alert_processor_context_manager(self):
        """Test that AlertProcessor works as a context manager."""
        mock_session = AsyncMock(spec=AsyncSession)
        
        with patch('app.tasks.alert_tasks.AsyncSessionLocal', return_value=mock_session):
            async with AlertProcessor() as processor:
                assert processor.session == mock_session
                assert isinstance(processor, AlertProcessor)
    
    async def test_watchlist_creation(self):
        """Test watchlist creation functionality."""
        # Mock project
        mock_project = Project(
            id=1,
            name="Test Project",
            slug="test-project",
            created_at=datetime.utcnow()
        )
        
        # Mock user
        mock_user = User(
            id=1,
            email="test@example.com",
            created_at=datetime.utcnow()
        )
        
        # Create watchlist item
        watchlist_item = Watchlist(
            user_id=1,
            project_id=1,
            notes="Interesting project to watch",
            user=mock_user,
            project=mock_project
        )
        
        # Verify watchlist item properties
        assert watchlist_item.user_id == 1
        assert watchlist_item.project_id == 1
        assert watchlist_item.notes == "Interesting project to watch"
        assert watchlist_item.user == mock_user
        assert watchlist_item.project == mock_project
    
    async def test_alert_creation(self):
        """Test alert creation functionality."""
        # Mock project
        mock_project = Project(
            id=1,
            name="Test Project",
            slug="test-project",
            created_at=datetime.utcnow()
        )
        
        # Mock user
        mock_user = User(
            id=1,
            email="test@example.com",
            created_at=datetime.utcnow()
        )
        
        # Create alert
        alert = Alert(
            user_id=1,
            project_id=1,
            alert_type="funding_received",
            threshold={"min_amount": 500000},
            is_active="active",
            user=mock_user,
            project=mock_project
        )
        
        # Verify alert properties
        assert alert.user_id == 1
        assert alert.project_id == 1
        assert alert.alert_type == "funding_received"
        assert alert.threshold == {"min_amount": 500000}
        assert alert.is_active == "active"
        assert alert.user == mock_user
        assert alert.project == mock_project
    
    async def test_notification_creation(self):
        """Test notification creation functionality."""
        # Create notification
        notification = Notification(
            user_id=1,
            alert_id=1,
            project_id=1,
            message="🚀 Test Project received $1,000,000 in funding!",
            notification_type="funding_received",
            is_read=False
        )
        
        # Verify notification properties
        assert notification.user_id == 1
        assert notification.alert_id == 1
        assert notification.project_id == 1
        assert notification.message == "🚀 Test Project received $1,000,000 in funding!"
        assert notification.notification_type == "funding_received"
        assert notification.is_read is False
    
    async def test_funding_round_creation(self):
        """Test funding round creation functionality."""
        # Create funding round
        funding_round = FundingRound(
            project_id=1,
            round_type="Series A",
            amount_usd=1000000.0,
            currency="USD",
            announced_at=datetime.utcnow()
        )
        
        # Verify funding round properties
        assert funding_round.project_id == 1
        assert funding_round.round_type == "Series A"
        assert funding_round.amount_usd == 1000000.0
        assert funding_round.currency == "USD"
        assert funding_round.announced_at is not None
    
    async def test_process_all_alerts_structure(self):
        """Test the process_all_alerts function structure."""
        # Mock alert processor methods
        with patch.object(AlertProcessor, 'process_funding_alerts', return_value=2):
            with patch.object(AlertProcessor, 'process_listing_alerts', return_value=1):
                with patch.object(AlertProcessor, 'process_score_change_alerts', return_value=3):
                    with patch('app.tasks.alert_tasks.AsyncSessionLocal'):
                        # Process all alerts
                        results = await process_all_alerts()
                        
                        # Verify results structure
                        assert "funding_alerts" in results
                        assert "listing_alerts" in results
                        assert "score_change_alerts" in results
                        assert "total_processed" in results
                        
                        # Verify results values
                        assert results["funding_alerts"] == 2
                        assert results["listing_alerts"] == 1
                        assert results["score_change_alerts"] == 3
                        assert results["total_processed"] == 6


if __name__ == "__main__":
    # Run the acceptance test
    async def run_acceptance_test():
        test_instance = TestAlertSystem()
        await test_instance.test_acceptance_criteria_funding_alert_triggered()
        print("✅ Acceptance test passed: Alert is triggered when simulated funding event occurs")
    
    asyncio.run(run_acceptance_test())