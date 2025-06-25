# celery_app.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_BROKER = os.getenv("REDIS_BROKER", "redis://localhost:6379/0")

celery_app = Celery("socialsuit", broker=REDIS_BROKER, backend=REDIS_BROKER)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)