"""Celery application configuration."""

from celery import Celery
from app.core.config import settings
from configs.vc_crawler_config import get_vc_celery_schedule

# Create Celery instance
celery_app = Celery(
    "suit_research",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.crawler_tasks",
        "app.tasks.research_tasks",
        "app.tasks.notification_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "health-check": {
        "task": "app.tasks.research_tasks.health_check_task",
        "schedule": 60.0,  # Every minute
    },
    "cleanup-old-data": {
        "task": "app.tasks.research_tasks.cleanup_old_data",
        "schedule": 3600.0,  # Every hour
    },
    "cleanup-old-crawler-data": {
        "task": "app.tasks.crawler_tasks.cleanup_old_crawler_data",
        "schedule": 86400.0,  # Every day
        "args": [30],  # Keep 30 days of data
    },
    "crawler-health-check": {
        "task": "app.tasks.crawler_tasks.health_check_crawler",
        "schedule": 300.0,  # Every 5 minutes
    },
    # TechCrunch RSS feeds
    "crawl-techcrunch-main": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": 7200.0,  # Every 2 hours
        "args": [
            "https://techcrunch.com/feed/",
            {
                "fetcher_type": "rss",
                "requests_per_second": 0.5,
                "timeout": 30,
                "respect_robots": True,
                "user_agent": "SuitResearch/1.0 (+https://example.com/bot)"
            }
        ],
    },
    "crawl-techcrunch-funding": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": 14400.0,  # Every 4 hours
        "args": [
            "https://techcrunch.com/category/funding/feed/",
            {
                "fetcher_type": "rss",
                "requests_per_second": 0.5,
                "timeout": 30,
                "respect_robots": True,
                "user_agent": "SuitResearch/1.0 (+https://example.com/bot)"
            }
        ],
    },
    "crawl-techcrunch-ai": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": 21600.0,  # Every 6 hours
        "args": [
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            {
                "fetcher_type": "rss",
                "requests_per_second": 0.5,
                "timeout": 30,
                "respect_robots": True,
                "user_agent": "SuitResearch/1.0 (+https://example.com/bot)"
            }
        ],
    },
}

# Add VC crawler schedules
vc_schedules = get_vc_celery_schedule()
celery_app.conf.beat_schedule.update(vc_schedules)

celery_app.conf.timezone = "UTC"