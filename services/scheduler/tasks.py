# services/scheduler/tasks.py

from celery import shared_task
from services.scheduler.platform_post import post_to_platform
from services.refresh.meta_refresh import refresh_meta_token
from services.refresh.linkedin_refresh import refresh_linkedin_token
from services.refresh.twitter_refresh import refresh_twitter_token
from services.refresh.youtube_refresh import refresh_youtube_token
from services.refresh.tiktok_refresh import refresh_tiktok_token

# OPTIONAL: Add these if you ever have refresh for Telegram/Farcaster
# from services.refresh.telegram_refresh import refresh_telegram_token
# from services.refresh.farcaster_refresh import refresh_farcaster_token

from services.scheduler.celery_beat_scheduler import beat_job


@shared_task
def schedule_post(platform, user_token, post_payload):
    """
    Runs when a scheduled post needs to be published.
    """
    try:
        result = post_to_platform(platform, user_token, post_payload)
        print(f"[{platform.upper()}] ✅ Post result:", result)
        return result
    except Exception as e:
        print(f"[{platform.upper()}] ❌ Post failed: {str(e)}")
        return {"error": str(e)}


@shared_task
def auto_refresh_tokens():
    """
    Periodic task: Refresh tokens for all supported platforms.
    """
    refresh_meta_token()
    refresh_linkedin_token()
    refresh_twitter_token()
    refresh_youtube_token()
    refresh_tiktok_token()
    # If you build these later:
    # refresh_telegram_token()
    # refresh_farcaster_token()

    print("[INFO] ✅ All tokens refreshed successfully.")


@shared_task
def scheduled_post_dispatcher():
    """
    Periodic task: Dispatch due scheduled posts.
    """
    print("[INFO] 🚀 Running scheduled post dispatcher...")
    beat_job()
    print("[INFO] ✅ Dispatcher run finished.")