# services/tests/test_auto_engagement.py

from social_suit.app.services.auto_engagement import auto_engage

def test_auto_engage():
    post = "Let's discuss blockchain technology!"
    engagement_post = auto_engage(post)
    print("Engagement Post:", engagement_post)
