"""
Base crawler class for web scraping.
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Base class for all crawlers."""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch(self, url: str, **kwargs) -> Optional[str]:
        """Fetch content from URL."""
        try:
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    @abstractmethod
    async def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl a URL and extract data."""
        pass
    
    def extract_metadata(self, url: str, content: str) -> Dict[str, Any]:
        """Extract basic metadata from content."""
        return {
            "url": url,
            "crawled_at": datetime.utcnow().isoformat(),
            "content_length": len(content) if content else 0,
            "crawler_type": self.__class__.__name__
        }


class GeneralCrawler(BaseCrawler):
    """General purpose web crawler."""
    
    async def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl a URL and extract basic information."""
        content = await self.fetch(url)
        
        if not content:
            return {
                "error": "Failed to fetch content",
                "url": url,
                "crawled_at": datetime.utcnow().isoformat()
            }
        
        # Basic extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""
        
        # Extract all text content
        text_content = soup.get_text()
        
        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        result = {
            "title": title_text,
            "description": description,
            "content": text_content[:5000],  # Limit content size
            "links": links[:50],  # Limit number of links
            "metadata": self.extract_metadata(url, content)
        }
        
        return result


class ResearchCrawler(BaseCrawler):
    """Specialized crawler for research content."""
    
    async def crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """Crawl research-specific content."""
        content = await self.fetch(url)
        
        if not content:
            return {
                "error": "Failed to fetch content",
                "url": url,
                "crawled_at": datetime.utcnow().isoformat()
            }
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract research-specific elements
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Look for abstract/summary
        abstract = ""
        abstract_selectors = [
            'div.abstract',
            'section.abstract',
            '.summary',
            '#abstract'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                abstract = element.get_text().strip()
                break
        
        # Extract authors
        authors = []
        author_selectors = [
            '.author',
            '.authors',
            '[class*="author"]'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                author_text = element.get_text().strip()
                if author_text and author_text not in authors:
                    authors.append(author_text)
        
        # Extract publication date
        pub_date = ""
        date_selectors = [
            'meta[name="citation_publication_date"]',
            'meta[name="DC.Date"]',
            '.publication-date',
            '.pub-date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                pub_date = element.get('content') or element.get_text().strip()
                break
        
        result = {
            "title": title_text,
            "abstract": abstract,
            "authors": authors,
            "publication_date": pub_date,
            "full_content": soup.get_text()[:10000],  # Larger content for research
            "metadata": self.extract_metadata(url, content)
        }
        
        return result