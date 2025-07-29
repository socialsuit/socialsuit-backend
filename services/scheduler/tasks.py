from celery import shared_task
from services.scheduler.platform_post import post_to_platform
from services.refresh.meta_refresh import refresh_meta_token
from services.refresh.linkedin_refresh import refresh_linkedin_token
from services.refresh.twitter_refresh import refresh_twitter_token
from services.refresh.youtube_refresh import refresh_youtube_token
from services.refresh.tiktok_refresh import refresh_tiktok_token

from services.scheduler.dispatcher import dispatch_scheduled_posts  # ✅ Directly use dispatcher, no loop!
from services.utils.logger_config import setup_logger

logger = setup_logger("scheduler_tasks")  # ✅ FIX: Proper logger name

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def schedule_post(self, platform, user_token, post_payload):
    """
    Runs when a scheduled post needs to be published.
    Retries up to 3 times if fails.
    """
    logger.info(f"[SCHEDULE_POST] Posting on platform: {platform}")

    try:
        result = post_to_platform(platform, user_token, post_payload)
        logger.info(f"[SCHEDULE_POST] Post success for {platform} — Response: {result}")
        return result

    except Exception as e:
        logger.exception(f"[SCHEDULE_POST] Post failed for {platform}: {e}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.critical(f"[SCHEDULE_POST] Max retries exceeded for platform: {platform}")
            return {"error": str(e)}


@shared_task
def auto_refresh_tokens():
    """
    Periodic Celery Beat task:
    Refresh tokens for all supported platforms.
    """
    logger.info("[REFRESH] Starting refresh of all platform tokens...")

    try:
        refresh_meta_token()
        refresh_linkedin_token()
        refresh_twitter_token()
        refresh_youtube_token()
        refresh_tiktok_token()
        logger.info("[REFRESH] All tokens refreshed successfully.")
    except Exception as e:
        logger.exception(f"[REFRESH] Token refresh failed: {e}")


@shared_task
def scheduled_post_dispatcher():
    """
    Periodic Celery Beat task:
    Find & dispatch due scheduled posts.
    """
    logger.info("[DISPATCHER] Running scheduled post dispatcher job...")
    try:
        dispatch_scheduled_posts()  # ✅ Call dispatcher directly
    except Exception as e:
        logger.exception(f"[DISPATCHER] Error during dispatcher: {e}")
    logger.info("[DISPATCHER] Dispatcher finished.")