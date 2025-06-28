# services/scheduler/dispatcher.py

from services.scheduler.tasks import schedule_post

def dispatch_scheduled_posts(posts: list):
    """
    posts = [
        {"platform": "instagram", "user_token": {...}, "post_payload": {...}},
        ...
    ]
    """
    for i, post in enumerate(posts):
        delay = i // 100  # 100 posts per second
        schedule_post.apply_async(
            args=(post["platform"], post["user_token"], post["post_payload"]),
            countdown=delay
        )
