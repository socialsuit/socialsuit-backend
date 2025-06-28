# services/scheduler/celery_beat_scheduler.py

import asyncio
from datetime import datetime
from services.scheduler.dispatcher import dispatch_scheduled_posts
from services.database.database import get_db_session
from services.models.scheduled_post_model import ScheduledPost, PostStatus

async def beat_job():
    db = get_db_session()
    now = datetime.utcnow()
    
    posts = db.query(ScheduledPost).filter(
        ScheduledPost.status == PostStatus.pending,
        ScheduledPost.scheduled_time <= now
    ).all()
    
    if posts:
        payload = []
        for post in posts:
            payload.append({
                "user_token": {
                    "access_token": "PLACEHOLDER",  # link to real token table
                    "page_id": "PLACEHOLDER",
                    "ig_user_id": "PLACEHOLDER"
                },
                "post_payload": {
                    "platform": post.platform,
                    **post.post_payload
                }
            })
            post.status = PostStatus.retry

        db.commit()
        dispatch_scheduled_posts(payload)

    db.close()
