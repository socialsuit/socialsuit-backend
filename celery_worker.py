# celery_worker.py
from celery_app import celery_app

if name == 'main':
    celery_app.start()