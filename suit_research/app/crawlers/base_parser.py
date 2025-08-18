"""
Base parser classes for extracting structured data from crawled content.
"""

import json
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup, Tag
import dateutil.parser

from .base_fetcher import FetchResult

logger = logging.getLogger(__name__)


class ParseResult:
    """Result of a parsing operation."""
    
    def __init__(self, url: str, data: Dict[str, Any], 
                 parser_type: str, parsed_at: datetime,
                 error: Optional[str] = None):
        self.url = url
        self.data = data
        self.parser_type = parser_type
        self.parsed_at = parsed_at
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "url": self.url,
            "data": self.data,
            "parser_type": self.parser_type,
            "parsed_at": self.parsed_at,
            "error": self.error
        }


class BaseParser(ABC):
    """Base class for all parsers."""
    
    def __init__(self):
        self.parser_name = self.__class__.__name__
    
    @abstractmethod
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse content and extract structured data."""
        pass
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')   # Zero-width space
        
        return text
    
    def _extract_date(self, date_str: str) -> Optional[datetime]:
        """Extract and parse date from string."""
        if not date_str:
            return None
        
        try:
            return dateutil.parser.parse(date_str)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
    
    def _resolve_url(self, base_url: str, url: str) -> str:
        """Resolve relative URLs to absolute URLs."""
        if not url:
            return ""
        return urljoin(base_url, url)


class HTMLParser(BaseParser):
    """Parser for HTML content."""
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse HTML content and extract structured data."""
        parsed_at = datetime.utcnow()
        
        if fetch_result.error:
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=fetch_result.error
            )
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'html.parser')
            
            # Extract basic metadata
            data = {
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "author": self._extract_author(soup),
                "published_date": self._extract_published_date(soup),
                "modified_date": self._extract_modified_date(soup),
                "canonical_url": self._extract_canonical_url(soup, fetch_result.url),
                "language": self._extract_language(soup),
                "keywords": self._extract_keywords(soup),
                "images": self._extract_images(soup, fetch_result.url),
                "links": self._extract_links(soup, fetch_result.url),
                "content": self._extract_content(soup),
                "word_count": self._calculate_word_count(soup),
                "meta_tags": self._extract_meta_tags(soup),
                "structured_data": self._extract_structured_data(soup)
            }
            
            return ParseResult(
                url=fetch_result.url,
                data=data,
                parser_type=self.parser_name,
                parsed_at=parsed_at
            )
            
        except Exception as e:
            logger.error(f"Error parsing HTML from {fetch_result.url}: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=str(e)
            )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try different title sources
        title_sources = [
            soup.find('meta', property='og:title'),
            soup.find('meta', name='twitter:title'),
            soup.find('title'),
            soup.find('h1')
        ]
        
        for source in title_sources:
            if source:
                if source.name == 'meta':
                    title = source.get('content', '')
                else:
                    title = source.get_text()
                
                if title:
                    return self._clean_text(title)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        desc_sources = [
            soup.find('meta', name='description'),
            soup.find('meta', property='og:description'),
            soup.find('meta', name='twitter:description')
        ]
        
        for source in desc_sources:
            if source:
                desc = source.get('content', '')
                if desc:
                    return self._clean_text(desc)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information."""
        author_sources = [
            soup.find('meta', name='author'),
            soup.find('meta', property='article:author'),
            soup.find('meta', name='twitter:creator'),
            soup.find(class_=re.compile(r'author', re.I)),
            soup.find('span', class_=re.compile(r'byline', re.I))
        ]
        
        for source in author_sources:
            if source:
                if source.name == 'meta':
                    author = source.get('content', '')
                else:
                    author = source.get_text()
                
                if author:
                    return self._clean_text(author)
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date."""
        date_sources = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', name='publication_date'),
            soup.find('time', attrs={'datetime': True}),
            soup.find(class_=re.compile(r'date|publish', re.I))
        ]
        
        for source in date_sources:
            if source:
                if source.name == 'meta':
                    date_str = source.get('content', '')
                elif source.name == 'time':
                    date_str = source.get('datetime', '') or source.get_text()
                else:
                    date_str = source.get_text()
                
                if date_str:
                    return self._extract_date(date_str)
        
        return None
    
    def _extract_modified_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract last modified date."""
        date_sources = [
            soup.find('meta', property='article:modified_time'),
            soup.find('meta', name='last-modified')
        ]
        
        for source in date_sources:
            if source:
                date_str = source.get('content', '')
                if date_str:
                    return self._extract_date(date_str)
        
        return None
    
    def _extract_canonical_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extract canonical URL."""
        canonical = soup.find('link', rel='canonical')
        if canonical:
            href = canonical.get('href', '')
            if href:
                return self._resolve_url(base_url, href)
        
        return base_url
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract page language."""
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang', '')
            if lang:
                return lang
        
        lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_meta:
            return lang_meta.get('content', '')
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords."""
        keywords_meta = soup.find('meta', name='keywords')
        if keywords_meta:
            keywords_str = keywords_meta.get('content', '')
            if keywords_str:
                return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        
        return []
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract images with metadata."""
        images = []
        
        # Extract from meta tags
        og_image = soup.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content', '')
            if img_url:
                images.append({
                    'url': self._resolve_url(base_url, img_url),
                    'type': 'og:image',
                    'alt': ''
                })
        
        # Extract from img tags (limit to avoid too much data)
        img_tags = soup.find_all('img', src=True)[:10]
        for img in img_tags:
            src = img.get('src', '')
            if src:
                images.append({
                    'url': self._resolve_url(base_url, src),
                    'type': 'content',
                    'alt': img.get('alt', '')
                })
        
        return images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links (limit to avoid too much data)."""
        links = []
        link_tags = soup.find_all('a', href=True)[:20]
        
        for link in link_tags:
            href = link.get('href', '')
            if href:
                links.append({
                    'url': self._resolve_url(base_url, href),
                    'text': self._clean_text(link.get_text()),
                    'title': link.get('title', '')
                })
        
        return links
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content text."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content area
        content_selectors = [
            'article',
            'main',
            '.content',
            '.post-content',
            '.entry-content',
            '#content'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                return self._clean_text(content_elem.get_text())
        
        # Fallback to body text
        body = soup.find('body')
        if body:
            return self._clean_text(body.get_text())
        
        return self._clean_text(soup.get_text())
    
    def _calculate_word_count(self, soup: BeautifulSoup) -> int:
        """Calculate word count of content."""
        content = self._extract_content(soup)
        if content:
            return len(content.split())
        return 0
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract all meta tags."""
        meta_tags = {}
        
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            
            if name and content:
                meta_tags[name] = content
        
        return meta_tags
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract JSON-LD structured data."""
        structured_data = []
        
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return structured_data


class RSSParser(BaseParser):
    """Parser for RSS feeds."""
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse RSS feed and extract structured data."""
        parsed_at = datetime.utcnow()
        
        if fetch_result.error:
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=fetch_result.error
            )
        
        try:
            feed = feedparser.parse(fetch_result.content)
            
            # Extract feed metadata
            feed_data = {
                "title": feed.feed.get('title', ''),
                "description": feed.feed.get('description', ''),
                "link": feed.feed.get('link', ''),
                "language": feed.feed.get('language', ''),
                "updated": self._extract_date(feed.feed.get('updated', '')),
                "generator": feed.feed.get('generator', ''),
                "image": self._extract_feed_image(feed.feed),
                "entries": []
            }
            
            # Extract entries
            for entry in feed.entries[:50]:  # Limit entries
                entry_data = {
                    "title": entry.get('title', ''),
                    "link": entry.get('link', ''),
                    "description": entry.get('description', ''),
                    "summary": entry.get('summary', ''),
                    "published": self._extract_date(entry.get('published', '')),
                    "updated": self._extract_date(entry.get('updated', '')),
                    "author": entry.get('author', ''),
                    "tags": [tag.term for tag in entry.get('tags', [])],
                    "guid": entry.get('guid', ''),
                    "content": self._extract_entry_content(entry)
                }
                feed_data["entries"].append(entry_data)
            
            return ParseResult(
                url=fetch_result.url,
                data=feed_data,
                parser_type=self.parser_name,
                parsed_at=parsed_at
            )
            
        except Exception as e:
            logger.error(f"Error parsing RSS from {fetch_result.url}: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=str(e)
            )
    
    def _extract_feed_image(self, feed_info: Dict[str, Any]) -> Dict[str, str]:
        """Extract feed image information."""
        image_info = {}
        
        if 'image' in feed_info:
            image = feed_info['image']
            if isinstance(image, dict):
                image_info = {
                    'url': image.get('href', ''),
                    'title': image.get('title', ''),
                    'link': image.get('link', '')
                }
        
        return image_info
    
    def _extract_entry_content(self, entry: Dict[str, Any]) -> str:
        """Extract full content from RSS entry."""
        # Try different content fields
        content_fields = ['content', 'summary_detail', 'description']
        
        for field in content_fields:
            if field in entry:
                content_data = entry[field]
                if isinstance(content_data, list) and content_data:
                    content_data = content_data[0]
                
                if isinstance(content_data, dict):
                    content = content_data.get('value', '')
                else:
                    content = str(content_data)
                
                if content:
                    return self._clean_text(content)
        
        return ""


class JSONParser(BaseParser):
    """Parser for JSON API responses."""
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse JSON content and extract structured data."""
        parsed_at = datetime.utcnow()
        
        if fetch_result.error:
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=fetch_result.error
            )
        
        try:
            data = json.loads(fetch_result.content)
            
            # For JSON, we mostly preserve the structure but add some metadata
            parsed_data = {
                "raw_data": data,
                "data_type": type(data).__name__,
                "keys": list(data.keys()) if isinstance(data, dict) else [],
                "length": len(data) if isinstance(data, (list, dict)) else 0,
                "schema": self._extract_schema(data)
            }
            
            return ParseResult(
                url=fetch_result.url,
                data=parsed_data,
                parser_type=self.parser_name,
                parsed_at=parsed_at
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {fetch_result.url}: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=f"JSON decode error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error processing JSON from {fetch_result.url}: {e}")
            return ParseResult(
                url=fetch_result.url,
                data={},
                parser_type=self.parser_name,
                parsed_at=parsed_at,
                error=str(e)
            )
    
    def _extract_schema(self, data: Any, max_depth: int = 3) -> Dict[str, Any]:
        """Extract schema information from JSON data."""
        if max_depth <= 0:
            return {"type": type(data).__name__}
        
        if isinstance(data, dict):
            schema = {"type": "object", "properties": {}}
            for key, value in data.items():
                schema["properties"][key] = self._extract_schema(value, max_depth - 1)
            return schema
        
        elif isinstance(data, list):
            schema = {"type": "array"}
            if data:
                # Use first item as example
                schema["items"] = self._extract_schema(data[0], max_depth - 1)
            return schema
        
        else:
            return {"type": type(data).__name__}


class GenericParser:
    """Generic parser that routes to appropriate parser based on content type."""
    
    def __init__(self):
        self.html_parser = HTMLParser()
        self.rss_parser = RSSParser()
        self.json_parser = JSONParser()
    
    async def parse(self, fetch_result: FetchResult) -> ParseResult:
        """Parse content using appropriate parser."""
        content_type = fetch_result.content_type.lower()
        
        if 'application/json' in content_type:
            return await self.json_parser.parse(fetch_result)
        elif any(rss_type in content_type for rss_type in 
                ['application/rss+xml', 'application/xml', 'text/xml']):
            return await self.rss_parser.parse(fetch_result)
        else:
            return await self.html_parser.parse(fetch_result)