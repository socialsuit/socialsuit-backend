# celery_app.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_BROKER = os.getenv("REDIS_BROKER", "redis://localhost:6379/0")

celery_app = Celery(
    "socialsuit",
    broker=REDIS_BROKER,
    backend=REDIS_BROKER,
    include=[
        "services.scheduler.tasks"  # Jahan tasks hain, wo import zaroor ho
    ]
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        "refresh-tokens-every-2-hours": {
            "task": "services.scheduler.tasks.auto_refresh_tokens",
            "schedule": 7200,  # every 2 hours
        },
        "dispatch-scheduled-posts-every-1-minute": {
            "task": "services.scheduler.tasks.scheduled_post_dispatcher",
            "schedule": 60,  # every minute
        },
    }
)