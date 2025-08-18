"""
TechCrunch RSS Crawler Configuration

This configuration demonstrates how to set up a crawler for TechCrunch RSS feeds
using the modular crawler framework.
"""

from datetime import timedelta
from typing import Dict, Any

# TechCrunch RSS Feed URLs
TECHCRUNCH_FEEDS = {
    "main": "https://techcrunch.com/feed/",
    "startups": "https://techcrunch.com/category/startups/feed/",
    "funding": "https://techcrunch.com/category/funding/feed/",
    "ai": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "apps": "https://techcrunch.com/category/apps/feed/",
    "security": "https://techcrunch.com/category/security/feed/",
    "enterprise": "https://techcrunch.com/category/enterprise/feed/",
    "gadgets": "https://techcrunch.com/category/gadgets/feed/",
}

# Base crawler configuration for TechCrunch
TECHCRUNCH_CONFIG = {
    "fetcher_type": "rss",
    "requests_per_second": 0.5,  # Be respectful - 1 request every 2 seconds
    "timeout": 30,
    "respect_robots": True,
    "user_agent": "SuitResearch/1.0 (+https://example.com/bot)"
}

# Celery Beat schedule for periodic crawling
TECHCRUNCH_SCHEDULE = {
    "crawl-techcrunch-main": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": timedelta(hours=2),  # Every 2 hours
        "args": [TECHCRUNCH_FEEDS["main"], TECHCRUNCH_CONFIG],
        "options": {
            "queue": "crawler",
            "routing_key": "crawler.rss"
        }
    },
    "crawl-techcrunch-funding": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task", 
        "schedule": timedelta(hours=4),  # Every 4 hours
        "args": [TECHCRUNCH_FEEDS["funding"], TECHCRUNCH_CONFIG],
        "options": {
            "queue": "crawler",
            "routing_key": "crawler.rss"
        }
    },
    "crawl-techcrunch-ai": {
        "task": "app.tasks.crawler_tasks.crawl_rss_feed_task",
        "schedule": timedelta(hours=6),  # Every 6 hours
        "args": [TECHCRUNCH_FEEDS["ai"], TECHCRUNCH_CONFIG],
        "options": {
            "queue": "crawler",
            "routing_key": "crawler.rss"
        }
    }
}

def get_techcrunch_config(feed_name: str = "main") -> Dict[str, Any]:
    """
    Get TechCrunch crawler configuration for a specific feed.
    
    Args:
        feed_name: Name of the feed (main, startups, funding, ai, etc.)
        
    Returns:
        Dictionary containing feed URL and crawler configuration
    """
    if feed_name not in TECHCRUNCH_FEEDS:
        raise ValueError(f"Unknown feed: {feed_name}. Available feeds: {list(TECHCRUNCH_FEEDS.keys())}")
    
    return {
        "url": TECHCRUNCH_FEEDS[feed_name],
        "config": TECHCRUNCH_CONFIG.copy()
    }

def get_all_techcrunch_feeds() -> Dict[str, Dict[str, Any]]:
    """
    Get all TechCrunch feed configurations.
    
    Returns:
        Dictionary mapping feed names to their configurations
    """
    return {
        name: get_techcrunch_config(name) 
        for name in TECHCRUNCH_FEEDS.keys()
    }

# Example usage functions
def crawl_techcrunch_main():
    """Example function to crawl TechCrunch main feed."""
    from app.tasks.crawler_tasks import crawl_rss_feed_task
    
    config = get_techcrunch_config("main")
    return crawl_rss_feed_task.delay(config["url"], config["config"])

def crawl_techcrunch_funding():
    """Example function to crawl TechCrunch funding feed."""
    from app.tasks.crawler_tasks import crawl_rss_feed_task
    
    config = get_techcrunch_config("funding")
    return crawl_rss_feed_task.delay(config["url"], config["config"])

def crawl_all_techcrunch_feeds():
    """Example function to crawl all TechCrunch feeds."""
    from app.tasks.crawler_tasks import crawl_rss_feed_task
    
    results = []
    for name, config in get_all_techcrunch_feeds().items():
        result = crawl_rss_feed_task.delay(config["url"], config["config"])
        results.append((name, result))
    
    return results

# Configuration for testing
TEST_CONFIG = {
    "url": TECHCRUNCH_FEEDS["main"],
    "config": {
        **TECHCRUNCH_CONFIG,
        "requests_per_second": 2.0,  # Faster for testing
        "timeout": 15
    }
}