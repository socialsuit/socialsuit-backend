from datetime import datetime
import logging
from services.scheduler.dispatcher import dispatch_scheduled_posts
from services.database.database import get_db_session
from services.models.scheduled_post_model import ScheduledPost, PostStatus
from services.utils.logger_config import setup_logger

logger = setup_logger(__name__)

async def beat_job():
    """
    Runs every X minutes: finds due scheduled posts and dispatches them.
    Runs inside Celery Beat.
    """
    db = get_db_session()
    try:
        now = datetime.utcnow()

        posts = db.query(ScheduledPost).filter(
            ScheduledPost.status == PostStatus.pending,
            ScheduledPost.scheduled_time <= now
        ).all()

        logger.info(f"[BEAT_JOB] Found {len(posts)} scheduled posts to dispatch.")

        if posts:
            payload = []
            for post in posts:
                logger.info(f"[BEAT_JOB] Dispatching post ID: {post.id} — Platform: {post.platform}")

                payload.append({
                    "user_token": {
                        "access_token": "PLACEHOLDER",
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
            logger.info(f"[BEAT_JOB] Committed status updates for {len(posts)} posts.")

            await dispatch_scheduled_posts(payload)  # This must also be async
            logger.info(f"[BEAT_JOB] Dispatch complete for batch.")

        else:
            logger.info("[BEAT_JOB] No pending posts at this time.")

    except Exception as e:
        logger.exception(f"[BEAT_JOB] Exception occurred: {e}")

    finally:
        db.close()
        logger.info("[BEAT_JOB] DB session closed.")