# services/scheduler/platform_post.py

from services.platforms.facebook_post import call_facebook_post
from services.platforms.instagram_post import call_instagram_post
from services.platforms.twitter_post import call_twitter_post
from services.platforms.linkedin_post import call_linkedin_post
from services.platforms.youtube_post import call_youtube_post
from services.platforms.tiktok_post import call_tiktok_post
from services.platforms.farcaster_post import call_farcaster_post

def post_to_platform(platform: str, user_token: dict, post_payload: dict):
    platform = platform.lower()

    if platform == "facebook":
        return call_facebook_post(user_token, post_payload)
    elif platform == "instagram":
        return call_instagram_post(user_token, post_payload)
    elif platform == "twitter":
        return call_twitter_post(user_token, post_payload)
    elif platform == "linkedin":
        return call_linkedin_post(user_token, post_payload)
    elif platform == "youtube":
        return call_youtube_post(user_token, post_payload)
    elif platform == "tiktok":
        return call_tiktok_post(user_token, post_payload)
    elif platform == "farcaster":
        return call_farcaster_post(user_token, post_payload)
    else:
        return {"error": f"Unsupported platform: {platform}"}
