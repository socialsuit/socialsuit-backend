from services.scheduler.tasks import schedule_post
import time

def dispatch_scheduled_posts(posts: list):
    """
    posts = [
        { "user_token": {...}, "post_payload": {...} },
        ...
    ]
    """
    for i, post in enumerate(posts):
        delay = i // 100  # 100 per second
        schedule_post.apply_async(args=(post["user_token"], post["post_payload"]), countdown=delay)