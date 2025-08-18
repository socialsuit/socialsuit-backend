"""
Base fetcher class for web crawling with support for HTML, RSS, JSON APIs.
Respects robots.txt and implements rate limiting.
"""

import asyncio
import aiohttp
import feedparser
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to respect website rate limits."""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
    
    async def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()


class RobotsChecker:
    """Check robots.txt compliance."""
    
    def __init__(self):
        self._robots_cache = {}
        self._cache_expiry = {}
        self.cache_duration = timedelta(hours=24)
    
    async def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """Check if URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            robots_url = urljoin(base_url, "/robots.txt")
            
            # Check cache
            if robots_url in self._robots_cache:
                if datetime.now() < self._cache_expiry[robots_url]:
                    rp = self._robots_cache[robots_url]
                    return rp.can_fetch(user_agent, url)
            
            # Fetch robots.txt
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(robots_url, timeout=10) as response:
                        if response.status == 200:
                            robots_content = await response.text()
                        else:
                            # If robots.txt doesn't exist, allow crawling
                            return True
                except:
                    # If can't fetch robots.txt, allow crawling
                    return True
            
            # Parse robots.txt
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # Cache the result
            self._robots_cache[robots_url] = rp
            self._cache_expiry[robots_url] = datetime.now() + self.cache_duration
            
            return rp.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If there's an error, allow crawling
            return True


class FetchResult:
    """Result of a fetch operation."""
    
    def __init__(self, url: str, content: str, content_type: str, 
                 status_code: int, headers: Dict[str, str], 
                 fetch_time: datetime, error: Optional[str] = None):
        self.url = url
        self.content = content
        self.content_type = content_type
        self.status_code = status_code
        self.headers = headers
        self.fetch_time = fetch_time
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "url": self.url,
            "content": self.content,
            "content_type": self.content_type,
            "status_code": self.status_code,
            "headers": dict(self.headers),
            "fetch_time": self.fetch_time,
            "error": self.error
        }


class BaseFetcher(ABC):
    """Base class for all fetchers."""
    
    def __init__(self, 
                 user_agent: str = "SuitResearch/1.0 (+https://suitresearch.com/bot)",
                 requests_per_second: float = 1.0,
                 timeout: int = 30,
                 respect_robots: bool = True):
        self.user_agent = user_agent
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.rate_limiter = RateLimiter(requests_per_second)
        self.robots_checker = RobotsChecker() if respect_robots else None
        
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched."""
        if not self.respect_robots or not self.robots_checker:
            return True
        return await self.robots_checker.can_fetch(url, self.user_agent)
    
    @abstractmethod
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch content from URL."""
        pass


class HTMLFetcher(BaseFetcher):
    """Fetcher for HTML pages."""
    
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch HTML content from URL."""
        fetch_time = datetime.utcnow()
        
        # Check robots.txt
        if not await self.can_fetch(url):
            return FetchResult(
                url=url, content="", content_type="text/html",
                status_code=403, headers={}, fetch_time=fetch_time,
                error="Blocked by robots.txt"
            )
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, **kwargs) as response:
                    content = await response.text()
                    
                    return FetchResult(
                        url=url,
                        content=content,
                        content_type=response.headers.get('content-type', 'text/html'),
                        status_code=response.status,
                        headers=dict(response.headers),
                        fetch_time=fetch_time
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching HTML from {url}: {e}")
            return FetchResult(
                url=url, content="", content_type="text/html",
                status_code=0, headers={}, fetch_time=fetch_time,
                error=str(e)
            )


class RSSFetcher(BaseFetcher):
    """Fetcher for RSS feeds."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.headers['Accept'] = 'application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8'
    
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch RSS feed from URL."""
        fetch_time = datetime.utcnow()
        
        # Check robots.txt
        if not await self.can_fetch(url):
            return FetchResult(
                url=url, content="", content_type="application/rss+xml",
                status_code=403, headers={}, fetch_time=fetch_time,
                error="Blocked by robots.txt"
            )
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, **kwargs) as response:
                    content = await response.text()
                    
                    # Validate RSS content
                    try:
                        # Parse with feedparser to validate
                        feed = feedparser.parse(content)
                        if feed.bozo and feed.bozo_exception:
                            logger.warning(f"RSS feed has issues: {feed.bozo_exception}")
                    except Exception as e:
                        logger.warning(f"RSS validation warning for {url}: {e}")
                    
                    return FetchResult(
                        url=url,
                        content=content,
                        content_type=response.headers.get('content-type', 'application/rss+xml'),
                        status_code=response.status,
                        headers=dict(response.headers),
                        fetch_time=fetch_time
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching RSS from {url}: {e}")
            return FetchResult(
                url=url, content="", content_type="application/rss+xml",
                status_code=0, headers={}, fetch_time=fetch_time,
                error=str(e)
            )


class JSONAPIFetcher(BaseFetcher):
    """Fetcher for JSON APIs."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.headers['Accept'] = 'application/json,*/*;q=0.8'
        self.headers['Content-Type'] = 'application/json'
    
    async def fetch(self, url: str, method: str = 'GET', 
                   data: Optional[Dict[str, Any]] = None, **kwargs) -> FetchResult:
        """Fetch JSON data from API."""
        fetch_time = datetime.utcnow()
        
        # Check robots.txt
        if not await self.can_fetch(url):
            return FetchResult(
                url=url, content="", content_type="application/json",
                status_code=403, headers={}, fetch_time=fetch_time,
                error="Blocked by robots.txt"
            )
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                # Prepare request data
                request_kwargs = {'headers': self.headers, **kwargs}
                if data and method.upper() in ['POST', 'PUT', 'PATCH']:
                    request_kwargs['json'] = data
                
                async with session.request(method, url, **request_kwargs) as response:
                    content = await response.text()
                    
                    # Validate JSON content
                    try:
                        json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON from {url}: {e}")
                    
                    return FetchResult(
                        url=url,
                        content=content,
                        content_type=response.headers.get('content-type', 'application/json'),
                        status_code=response.status,
                        headers=dict(response.headers),
                        fetch_time=fetch_time
                    )
                    
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {e}")
            return FetchResult(
                url=url, content="", content_type="application/json",
                status_code=0, headers={}, fetch_time=fetch_time,
                error=str(e)
            )


class GenericFetcher(BaseFetcher):
    """Generic fetcher that auto-detects content type."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.html_fetcher = HTMLFetcher(**kwargs)
        self.rss_fetcher = RSSFetcher(**kwargs)
        self.json_fetcher = JSONAPIFetcher(**kwargs)
    
    def _detect_content_type(self, url: str, headers: Dict[str, str]) -> str:
        """Detect content type from URL and headers."""
        content_type = headers.get('content-type', '').lower()
        
        # Check content-type header
        if 'application/json' in content_type:
            return 'json'
        elif any(rss_type in content_type for rss_type in 
                ['application/rss+xml', 'application/xml', 'text/xml']):
            return 'rss'
        elif 'text/html' in content_type:
            return 'html'
        
        # Check URL patterns
        url_lower = url.lower()
        if url_lower.endswith('.json') or '/api/' in url_lower:
            return 'json'
        elif any(pattern in url_lower for pattern in ['/rss', '/feed', '.rss', '.xml']):
            return 'rss'
        
        # Default to HTML
        return 'html'
    
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        """Fetch content with auto-detection of content type."""
        
        # First, make a HEAD request to check content type
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url, headers=self.headers) as response:
                    content_type = self._detect_content_type(url, dict(response.headers))
        except:
            # If HEAD fails, guess from URL
            content_type = self._detect_content_type(url, {})
        
        # Use appropriate fetcher
        if content_type == 'json':
            return await self.json_fetcher.fetch(url, **kwargs)
        elif content_type == 'rss':
            return await self.rss_fetcher.fetch(url, **kwargs)
        else:
            return await self.html_fetcher.fetch(url, **kwargs)