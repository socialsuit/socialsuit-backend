# services/scheduler/tasks.py

from celery import shared_task
from services.scheduler.platform_post import post_to_platform

@shared_task
def schedule_post(platform, user_token, post_payload):
    try:
        result = post_to_platform(platform, user_token, post_payload)
        print(f"[{platform.upper()}] Post result:", result)
        return result
    except Exception as e:
        print(f"[ERROR] Failed to post on {platform}: {str(e)}")
        return {"error": str(e)}
    