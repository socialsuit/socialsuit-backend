# services/scheduler/celery_beat_scheduler.py

from datetime import datetime
from services.scheduler.dispatcher import dispatch_scheduled_posts
from services.database.database import get_db_session
from services.models.scheduled_post_model import ScheduledPost, PostStatus
from services.models.token_model import PlatformToken

def beat_job():
    """
    Runs every X minutes:
    - Finds due scheduled posts
    - Looks up user tokens for each platform
    - Dispatches them for posting
    Runs inside Celery Beat.
    """
    db = get_db_session()
    now = datetime.utcnow()

    due_posts = db.query(ScheduledPost).filter(
        ScheduledPost.status == PostStatus.pending,
        ScheduledPost.scheduled_time <= now
    ).all()

    if due_posts:
        payloads = []

        for post in due_posts:
            # ✅ 1️⃣ Find matching user token for this post's user + platform
            user_token = db.query(PlatformToken).filter(
                PlatformToken.user_id == post.user_id,
                PlatformToken.platform == post.platform.lower()
            ).first()

            if not user_token:
                print(f"[WARN] No token found for {post.platform} user={post.user_id}")
                continue

            # ✅ 2️⃣ Prepare payload
            payloads.append({
                "user_token": {
                    "access_token": user_token.access_token,
                    "refresh_token": user_token.refresh_token,
                    "channel_id": user_token.channel_id,
                    # Add more fields if needed (page_id, ig_user_id, etc)
                },
                "post_payload": {
                    "platform": post.platform,
                    **post.post_payload
                }
            })

            # ✅ 3️⃣ Mark post as processing/retry
            post.status = PostStatus.retry  # or PostStatus.processing

        db.commit()

        # ✅ 4️⃣ Dispatch batch to Celery workers
        dispatch_scheduled_posts(payloads)

    db.close()