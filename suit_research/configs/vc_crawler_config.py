#!/usr/bin/env python3
"""
Configuration for VC (Venture Capital) crawler.
Defines crawling schedules, settings, and parameters for VC firm crawling.
"""

from datetime import timedelta
from typing import Dict, Any, List

# VC Crawler Configuration
VC_CRAWLER_CONFIG = {
    'fetcher_type': 'html',
    'requests_per_second': 0.5,  # Conservative rate limiting
    'timeout': 30,
    'respect_robots': True,
    'user_agent': 'SuitResearch VC Crawler/1.0 (+https://suitresearch.com/bot)',
    'max_retries': 3,
    'retry_delay': 5,
    'max_pages_per_site': 20,  # Limit crawling depth
    'follow_redirects': True,
    'verify_ssl': True
}

# Celery Beat Schedule for VC Crawling
VC_CELERY_BEAT_SCHEDULE = {
    # Daily crawl of top 20 VC firms
    'crawl-top-vc-firms-daily': {
        'task': 'app.tasks.crawler_tasks.crawl_multiple_vc_firms_task',
        'schedule': timedelta(hours=24),  # Once per day
        'kwargs': {
            'limit': 20,
            'config': VC_CRAWLER_CONFIG
        },
        'options': {
            'queue': 'vc_crawler',
            'routing_key': 'vc_crawler',
            'priority': 5
        }
    },
    
    # Weekly comprehensive crawl of all VC firms
    'crawl-all-vc-firms-weekly': {
        'task': 'app.tasks.crawler_tasks.crawl_multiple_vc_firms_task',
        'schedule': timedelta(days=7),  # Once per week
        'kwargs': {
            'limit': 100,  # All firms
            'config': {
                **VC_CRAWLER_CONFIG,
                'requests_per_second': 0.3,  # Even more conservative for large batch
                'max_pages_per_site': 15
            }
        },
        'options': {
            'queue': 'vc_crawler',
            'routing_key': 'vc_crawler',
            'priority': 3
        }
    },
    
    # Cleanup old VC data monthly
    'cleanup-old-vc-data': {
        'task': 'app.tasks.crawler_tasks.cleanup_vc_data',
        'schedule': timedelta(days=30),  # Once per month
        'kwargs': {
            'days_to_keep': 90  # Keep 3 months of data
        },
        'options': {
            'queue': 'maintenance',
            'routing_key': 'maintenance',
            'priority': 1
        }
    }
}

# VC Firm Categories for Targeted Crawling
VC_CATEGORIES = {
    'tier1': {
        'description': 'Top-tier VC firms (Sequoia, A16z, etc.)',
        'crawl_frequency': timedelta(hours=12),  # Twice daily
        'priority': 10,
        'max_pages_per_site': 25
    },
    'tier2': {
        'description': 'Mid-tier VC firms',
        'crawl_frequency': timedelta(hours=24),  # Daily
        'priority': 7,
        'max_pages_per_site': 20
    },
    'emerging': {
        'description': 'Emerging and regional VC firms',
        'crawl_frequency': timedelta(days=3),  # Every 3 days
        'priority': 5,
        'max_pages_per_site': 15
    }
}

# URL Patterns for VC Site Discovery
VC_URL_PATTERNS = {
    'portfolio_keywords': [
        'portfolio', 'companies', 'investments', 'startups',
        'our-companies', 'our-portfolio', 'portfolio-companies'
    ],
    'press_keywords': [
        'news', 'press', 'announcements', 'blog', 'insights',
        'press-releases', 'media', 'updates', 'funding'
    ],
    'team_keywords': [
        'team', 'people', 'partners', 'about', 'leadership'
    ]
}

# Data Extraction Patterns
VC_EXTRACTION_PATTERNS = {
    'portfolio_selectors': [
        '.portfolio-company',
        '.company-item',
        '.portfolio-item',
        '[data-company]',
        '.startup',
        '.investment'
    ],
    'company_name_selectors': [
        'h1', 'h2', 'h3', '.company-name', '.name',
        '[data-name]', '.title', 'strong', 'b'
    ],
    'funding_amount_patterns': [
        r'\$([0-9]+(?:\.[0-9]+)?(?:[KMB]|\s*(?:million|billion|thousand)))',
        r'([0-9]+(?:\.[0-9]+)?)\s*(?:million|billion|thousand)',
        r'\$([0-9,]+(?:\.[0-9]+)?)',
        r'raised\s+\$([0-9,]+(?:\.[0-9]+)?(?:[KMB])?)',
        r'funding\s+of\s+\$([0-9,]+(?:\.[0-9]+)?(?:[KMB])?)',
        r'Series\s+[A-Z]\s+\$([0-9,]+(?:\.[0-9]+)?(?:[KMB])?)',
        r'round\s+of\s+\$([0-9,]+(?:\.[0-9]+)?(?:[KMB])?)',
    ],
    'round_type_patterns': [
        r'(Series\s+[A-Z]+)',
        r'(Seed|Pre-seed|Angel)',
        r'(IPO|Initial\s+Public\s+Offering)',
        r'(Bridge|Convertible)',
        r'(Growth|Late\s+Stage)',
        r'(Acquisition|Exit)'
    ]
}

# MongoDB Collection Names
VC_COLLECTIONS = {
    'investors': 'investors',
    'funding_rounds': 'funding_rounds',
    'vc_crawl_jobs': 'vc_crawl_jobs',
    'raw_crawls': 'raw_crawls'
}

# Error Handling Configuration
VC_ERROR_CONFIG = {
    'max_consecutive_failures': 5,
    'failure_backoff_multiplier': 2,
    'max_backoff_seconds': 300,
    'retry_on_status_codes': [429, 500, 502, 503, 504],
    'ignore_ssl_errors': False,
    'timeout_retry_count': 2
}

# Logging Configuration
VC_LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'logs/vc_crawler.log',
    'max_log_size': '10MB',
    'backup_count': 5
}


def get_vc_crawler_config(category: str = 'tier2') -> Dict[str, Any]:
    """
    Get VC crawler configuration for a specific category.
    
    Args:
        category: VC firm category ('tier1', 'tier2', 'emerging')
    
    Returns:
        Configuration dictionary
    """
    base_config = VC_CRAWLER_CONFIG.copy()
    
    if category in VC_CATEGORIES:
        category_config = VC_CATEGORIES[category]
        base_config.update({
            'max_pages_per_site': category_config['max_pages_per_site'],
            'priority': category_config['priority']
        })
    
    return base_config


def get_vc_celery_schedule() -> Dict[str, Any]:
    """
    Get the complete Celery Beat schedule for VC crawling.
    
    Returns:
        Celery Beat schedule dictionary
    """
    return VC_CELERY_BEAT_SCHEDULE


def get_extraction_patterns() -> Dict[str, Any]:
    """
    Get data extraction patterns for VC sites.
    
    Returns:
        Extraction patterns dictionary
    """
    return VC_EXTRACTION_PATTERNS


def get_url_discovery_patterns() -> Dict[str, List[str]]:
    """
    Get URL discovery patterns for VC sites.
    
    Returns:
        URL patterns dictionary
    """
    return VC_URL_PATTERNS


# Example usage functions
def create_vc_crawl_task(firm_name: str, website: str, category: str = 'tier2') -> Dict[str, Any]:
    """
    Create a VC crawl task configuration.
    
    Args:
        firm_name: Name of the VC firm
        website: Website URL
        category: VC firm category
    
    Returns:
        Task configuration
    """
    config = get_vc_crawler_config(category)
    
    return {
        'firm_name': firm_name,
        'website': website,
        'config': config,
        'category': category,
        'extraction_patterns': get_extraction_patterns(),
        'url_patterns': get_url_discovery_patterns()
    }


def get_priority_firms() -> List[str]:
    """
    Get list of priority VC firms for frequent crawling.
    
    Returns:
        List of firm names
    """
    return [
        'Sequoia Capital',
        'Andreessen Horowitz',
        'Accel',
        'Greylock Partners',
        'Kleiner Perkins',
        'Benchmark',
        'First Round Capital',
        'Union Square Ventures',
        'GV (Google Ventures)',
        'Intel Capital',
        'Bessemer Venture Partners',
        'NEA (New Enterprise Associates)',
        'Lightspeed Venture Partners',
        'General Catalyst',
        'Insight Partners',
        'Tiger Global Management',
        'Coatue Management',
        'DST Global',
        'SoftBank Vision Fund',
        'Y Combinator'
    ]