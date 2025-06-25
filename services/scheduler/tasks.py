from celery_app import celery_app
from services.scheduler.ustils import call_meta_api, RateLimitError

@celery_app.task(bind=True, autoretry_for=(RateLimitError,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def schedule_post(self, user_token: dict, post_payload: dict):
    result = call_meta_api(user_token["access_token"], post_payload)

    if "error" in result:
        raise RateLimitError(result["error"]["message"])
    
    # TODO: Log success in DB
    return result