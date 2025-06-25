#celery_beat_scheduler.py

import asyncio 
from datetime import datetime 
from services.scheduler.dispatcher import dispatch_scheduled_posts 
from services.database.database import get_db_session 
from services.models.scheduled_post_model import ScheduledPost, PostStatus 
from services.models.token_model import UserToken  # ⬅️ Import token model

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
        token = db.query(UserToken).filter_by(user_id=post.user_id, platform=post.platform).first()
        if not token:
            continue  # skip if token not found

        payload.append({
            "user_token": {
                "access_token": token.access_token
            },
            "post_payload": post.post_payload
        })
        post.status = PostStatus.retry  # Mark as in-progress

    db.commit()
    dispatch_scheduled_posts(payload)
db.close()