from celery import current_app

def dispatch_scheduled_posts(posts: list):
    """
    posts = [
        {"platform": "instagram", "user_token": {...}, "post_payload": {...}},
        ...
    ]
    """
    for i, post in enumerate(posts):
        delay = i // 100  # 100 posts per second

        current_app.send_task(
            'services.scheduler.tasks.schedule_post',
            args=(post["platform"], post["user_token"], post["post_payload"]),
            countdown=delay
        )