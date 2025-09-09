from fastapi import Depends
from sqlalchemy.orm import Session

from social_suit.app.services.database.database import get_db
from social_suit.app.services.repositories.user_repository import UserRepository
from social_suit.app.services.repositories.scheduled_post_repository import ScheduledPostRepository
from social_suit.app.services.repositories.analytics_repository import (
    PostEngagementRepository, 
    UserMetricsRepository, 
    ContentPerformanceRepository
)

# User repository provider
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """
    Dependency provider for UserRepository
    """
    return UserRepository(db)

# Scheduled post repository provider
def get_scheduled_post_repository(db: Session = Depends(get_db)) -> ScheduledPostRepository:
    """
    Dependency provider for ScheduledPostRepository
    """
    return ScheduledPostRepository(db)

# Analytics repositories providers
def get_post_engagement_repository(db: Session = Depends(get_db)) -> PostEngagementRepository:
    """
    Dependency provider for PostEngagementRepository
    """
    return PostEngagementRepository(db)

def get_user_metrics_repository(db: Session = Depends(get_db)) -> UserMetricsRepository:
    """
    Dependency provider for UserMetricsRepository
    """
    return UserMetricsRepository(db)

def get_content_performance_repository(db: Session = Depends(get_db)) -> ContentPerformanceRepository:
    """
    Dependency provider for ContentPerformanceRepository
    """
    return ContentPerformanceRepository(db)