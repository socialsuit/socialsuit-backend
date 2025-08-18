"""
Data normalizer classes for cleaning and mapping parsed data to database schema.
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urlparse

from .base_parser import ParseResult

logger = logging.getLogger(__name__)


class NormalizedData:
    """Container for normalized data ready for database storage."""
    
    def __init__(self, 
                 raw_crawl_data: Dict[str, Any],
                 structured_data: Optional[Dict[str, Any]] = None,
                 content_type: str = "unknown",
                 source_type: str = "web"):
        self.raw_crawl_data = raw_crawl_data
        self.structured_data = structured_data or {}
        self.content_type = content_type
        self.source_type = source_type
        self.normalized_at = datetime.utcnow()
    
    def to_raw_crawl_document(self) -> Dict[str, Any]:
        """Convert to RawCrawl MongoDB document format."""
        return {
            "raw_html": self.raw_crawl_data.get("content", ""),
            "source": self.raw_crawl_data.get("url", ""),
            "scraped_at": self.raw_crawl_data.get("fetch_time", datetime.utcnow()),
            "metadata": {
                "content_type": self.content_type,
                "source_type": self.source_type,
                "status_code": self.raw_crawl_data.get("status_code", 0),
                "headers": self.raw_crawl_data.get("headers", {}),
                "parser_type": self.raw_crawl_data.get("parser_type", "unknown"),
                "normalized_at": self.normalized_at,
                **self.raw_crawl_data.get("metadata", {})
            },
            "processed": False,
            "content_type": self.content_type,
            "language": self.structured_data.get("language", ""),
            "error": self.raw_crawl_data.get("error")
        }
    
    def to_structured_document(self) -> Dict[str, Any]:
        """Convert to structured data document for further processing."""
        return {
            "source_url": self.raw_crawl_data.get("url", ""),
            "title": self.structured_data.get("title", ""),
            "content": self.structured_data.get("content", ""),
            "summary": self.structured_data.get("description", ""),
            "author": self.structured_data.get("author", ""),
            "published_date": self.structured_data.get("published_date"),
            "modified_date": self.structured_data.get("modified_date"),
            "language": self.structured_data.get("language", ""),
            "keywords": self.structured_data.get("keywords", []),
            "images": self.structured_data.get("images", []),
            "links": self.structured_data.get("links", []),
            "word_count": self.structured_data.get("word_count", 0),
            "content_type": self.content_type,
            "source_type": self.source_type,
            "normalized_at": self.normalized_at,
            "metadata": self.structured_data.get("meta_tags", {})
        }


class BaseNormalizer(ABC):
    """Base class for all normalizers."""
    
    def __init__(self):
        self.normalizer_name = self.__class__.__name__
    
    @abstractmethod
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize parsed data to database schema."""
        pass
    
    def _clean_text(self, text: str, max_length: Optional[int] = None) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        text = text.replace('\u200b', '')   # Zero-width space
        text = text.replace('\ufeff', '')   # Byte order mark
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL format."""
        if not url:
            return ""
        
        # Remove fragment and normalize
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _detect_content_category(self, data: Dict[str, Any]) -> str:
        """Detect content category based on data."""
        title = data.get("title", "").lower()
        content = data.get("content", "").lower()
        url = data.get("url", "").lower()
        
        # Technology/startup keywords
        tech_keywords = [
            "startup", "funding", "investment", "venture", "vc", "seed",
            "series a", "series b", "ipo", "acquisition", "merger",
            "technology", "tech", "ai", "artificial intelligence", "ml",
            "blockchain", "crypto", "fintech", "saas", "api"
        ]
        
        # News keywords
        news_keywords = [
            "breaking", "news", "report", "announces", "launches",
            "releases", "update", "press release"
        ]
        
        # Research keywords
        research_keywords = [
            "research", "study", "analysis", "report", "whitepaper",
            "survey", "findings", "methodology", "data", "statistics"
        ]
        
        text_to_check = f"{title} {content[:500]}"
        
        if any(keyword in text_to_check for keyword in tech_keywords):
            return "technology"
        elif any(keyword in text_to_check for keyword in research_keywords):
            return "research"
        elif any(keyword in text_to_check for keyword in news_keywords):
            return "news"
        elif "/blog/" in url or "blog" in url:
            return "blog"
        else:
            return "general"
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract basic entities from text."""
        if not text:
            return {}
        
        entities = {
            "companies": [],
            "people": [],
            "technologies": [],
            "amounts": []
        }
        
        # Simple regex patterns for entity extraction
        # Company patterns (capitalized words followed by Inc, Corp, etc.)
        company_pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Technologies|Systems|Solutions)\b'
        entities["companies"] = list(set(re.findall(company_pattern, text)))
        
        # Money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|trillion|M|B|T))?'
        entities["amounts"] = list(set(re.findall(money_pattern, text, re.IGNORECASE)))
        
        # Technology terms
        tech_terms = [
            "AI", "artificial intelligence", "machine learning", "ML", "blockchain",
            "cryptocurrency", "API", "SaaS", "cloud computing", "IoT", "5G",
            "virtual reality", "VR", "augmented reality", "AR", "fintech"
        ]
        
        for term in tech_terms:
            if term.lower() in text.lower():
                entities["technologies"].append(term)
        
        return entities


class HTMLNormalizer(BaseNormalizer):
    """Normalizer for HTML content."""
    
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize HTML parse result."""
        try:
            data = parse_result.data
            
            # Create raw crawl data
            raw_crawl_data = {
                "url": parse_result.url,
                "content": data.get("content", ""),
                "fetch_time": parse_result.parsed_at,
                "parser_type": parse_result.parser_type,
                "error": parse_result.error,
                "metadata": {
                    "word_count": data.get("word_count", 0),
                    "images_count": len(data.get("images", [])),
                    "links_count": len(data.get("links", [])),
                    "has_structured_data": bool(data.get("structured_data"))
                }
            }
            
            # Create structured data
            structured_data = {
                "title": self._clean_text(data.get("title", ""), max_length=500),
                "description": self._clean_text(data.get("description", ""), max_length=1000),
                "content": self._clean_text(data.get("content", ""), max_length=50000),
                "author": self._clean_text(data.get("author", ""), max_length=200),
                "published_date": data.get("published_date"),
                "modified_date": data.get("modified_date"),
                "canonical_url": self._normalize_url(data.get("canonical_url", "")),
                "language": data.get("language", ""),
                "keywords": data.get("keywords", [])[:20],  # Limit keywords
                "images": self._normalize_images(data.get("images", [])[:10]),  # Limit images
                "links": self._normalize_links(data.get("links", [])[:20]),  # Limit links
                "word_count": data.get("word_count", 0),
                "meta_tags": data.get("meta_tags", {}),
                "structured_data": data.get("structured_data", []),
                "domain": self._extract_domain(parse_result.url),
                "content_category": self._detect_content_category(data),
                "entities": self._extract_entities(data.get("content", ""))
            }
            
            return NormalizedData(
                raw_crawl_data=raw_crawl_data,
                structured_data=structured_data,
                content_type="html",
                source_type="web"
            )
            
        except Exception as e:
            logger.error(f"Error normalizing HTML data from {parse_result.url}: {e}")
            # Return minimal data on error
            return NormalizedData(
                raw_crawl_data={
                    "url": parse_result.url,
                    "content": "",
                    "fetch_time": parse_result.parsed_at,
                    "parser_type": parse_result.parser_type,
                    "error": str(e)
                },
                content_type="html",
                source_type="web"
            )
    
    def _normalize_images(self, images: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Normalize image data."""
        normalized = []
        for img in images:
            if img.get("url"):
                normalized.append({
                    "url": self._normalize_url(img["url"]),
                    "alt": self._clean_text(img.get("alt", ""), max_length=200),
                    "type": img.get("type", "content")
                })
        return normalized
    
    def _normalize_links(self, links: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Normalize link data."""
        normalized = []
        seen_urls = set()
        
        for link in links:
            url = link.get("url", "")
            if url and url not in seen_urls:
                normalized.append({
                    "url": self._normalize_url(url),
                    "text": self._clean_text(link.get("text", ""), max_length=200),
                    "title": self._clean_text(link.get("title", ""), max_length=200)
                })
                seen_urls.add(url)
        
        return normalized


class RSSNormalizer(BaseNormalizer):
    """Normalizer for RSS feed content."""
    
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize RSS parse result."""
        try:
            data = parse_result.data
            
            # For RSS, we create multiple documents - one for the feed and one for each entry
            feed_data = {
                "url": parse_result.url,
                "content": str(data),  # Store full feed data as content
                "fetch_time": parse_result.parsed_at,
                "parser_type": parse_result.parser_type,
                "error": parse_result.error,
                "metadata": {
                    "feed_title": data.get("title", ""),
                    "feed_description": data.get("description", ""),
                    "entries_count": len(data.get("entries", [])),
                    "feed_language": data.get("language", ""),
                    "feed_updated": data.get("updated")
                }
            }
            
            # Create structured data for the feed
            structured_data = {
                "title": self._clean_text(data.get("title", ""), max_length=500),
                "description": self._clean_text(data.get("description", ""), max_length=1000),
                "content": self._create_feed_summary(data),
                "language": data.get("language", ""),
                "published_date": data.get("updated"),
                "domain": self._extract_domain(parse_result.url),
                "content_category": "rss_feed",
                "feed_info": {
                    "generator": data.get("generator", ""),
                    "link": data.get("link", ""),
                    "image": data.get("image", {}),
                    "entries_count": len(data.get("entries", []))
                },
                "entries": self._normalize_entries(data.get("entries", []))
            }
            
            return NormalizedData(
                raw_crawl_data=feed_data,
                structured_data=structured_data,
                content_type="rss",
                source_type="feed"
            )
            
        except Exception as e:
            logger.error(f"Error normalizing RSS data from {parse_result.url}: {e}")
            return NormalizedData(
                raw_crawl_data={
                    "url": parse_result.url,
                    "content": "",
                    "fetch_time": parse_result.parsed_at,
                    "parser_type": parse_result.parser_type,
                    "error": str(e)
                },
                content_type="rss",
                source_type="feed"
            )
    
    def _create_feed_summary(self, data: Dict[str, Any]) -> str:
        """Create a summary of the RSS feed."""
        entries = data.get("entries", [])
        if not entries:
            return data.get("description", "")
        
        summary_parts = [
            f"RSS feed with {len(entries)} entries.",
            f"Latest entry: {entries[0].get('title', 'Untitled')}" if entries else "",
            data.get("description", "")
        ]
        
        return " ".join(filter(None, summary_parts))
    
    def _normalize_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize RSS entries."""
        normalized = []
        
        for entry in entries[:50]:  # Limit entries
            normalized_entry = {
                "title": self._clean_text(entry.get("title", ""), max_length=500),
                "link": self._normalize_url(entry.get("link", "")),
                "description": self._clean_text(entry.get("description", ""), max_length=2000),
                "summary": self._clean_text(entry.get("summary", ""), max_length=2000),
                "content": self._clean_text(entry.get("content", ""), max_length=10000),
                "author": self._clean_text(entry.get("author", ""), max_length=200),
                "published_date": entry.get("published"),
                "updated_date": entry.get("updated"),
                "tags": entry.get("tags", [])[:10],  # Limit tags
                "guid": entry.get("guid", ""),
                "entities": self._extract_entities(entry.get("content", "") or entry.get("description", ""))
            }
            normalized.append(normalized_entry)
        
        return normalized


class JSONNormalizer(BaseNormalizer):
    """Normalizer for JSON API content."""
    
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize JSON parse result."""
        try:
            data = parse_result.data
            raw_data = data.get("raw_data", {})
            
            # Create raw crawl data
            raw_crawl_data = {
                "url": parse_result.url,
                "content": str(raw_data),  # Store JSON as string
                "fetch_time": parse_result.parsed_at,
                "parser_type": parse_result.parser_type,
                "error": parse_result.error,
                "metadata": {
                    "data_type": data.get("data_type", ""),
                    "keys": data.get("keys", []),
                    "length": data.get("length", 0),
                    "schema": data.get("schema", {})
                }
            }
            
            # Create structured data
            structured_data = {
                "title": self._extract_title_from_json(raw_data),
                "description": self._extract_description_from_json(raw_data),
                "content": self._create_json_summary(raw_data),
                "domain": self._extract_domain(parse_result.url),
                "content_category": "api_data",
                "json_schema": data.get("schema", {}),
                "data_structure": {
                    "type": data.get("data_type", ""),
                    "keys": data.get("keys", [])[:20],  # Limit keys
                    "length": data.get("length", 0)
                },
                "raw_json": raw_data
            }
            
            return NormalizedData(
                raw_crawl_data=raw_crawl_data,
                structured_data=structured_data,
                content_type="json",
                source_type="api"
            )
            
        except Exception as e:
            logger.error(f"Error normalizing JSON data from {parse_result.url}: {e}")
            return NormalizedData(
                raw_crawl_data={
                    "url": parse_result.url,
                    "content": "",
                    "fetch_time": parse_result.parsed_at,
                    "parser_type": parse_result.parser_type,
                    "error": str(e)
                },
                content_type="json",
                source_type="api"
            )
    
    def _extract_title_from_json(self, data: Any) -> str:
        """Extract title from JSON data."""
        if isinstance(data, dict):
            # Look for common title fields
            title_fields = ["title", "name", "headline", "subject", "label"]
            for field in title_fields:
                if field in data and isinstance(data[field], str):
                    return self._clean_text(data[field], max_length=500)
        
        return "JSON API Data"
    
    def _extract_description_from_json(self, data: Any) -> str:
        """Extract description from JSON data."""
        if isinstance(data, dict):
            # Look for common description fields
            desc_fields = ["description", "summary", "abstract", "content", "body"]
            for field in desc_fields:
                if field in data and isinstance(data[field], str):
                    return self._clean_text(data[field], max_length=1000)
        
        return f"JSON data with {len(data)} items" if isinstance(data, (list, dict)) else "JSON API response"
    
    def _create_json_summary(self, data: Any) -> str:
        """Create a summary of JSON data."""
        if isinstance(data, dict):
            keys = list(data.keys())[:10]  # First 10 keys
            return f"JSON object with keys: {', '.join(keys)}"
        elif isinstance(data, list):
            return f"JSON array with {len(data)} items"
        else:
            return f"JSON {type(data).__name__}: {str(data)[:200]}"


class GenericNormalizer:
    """Generic normalizer that routes to appropriate normalizer based on content type."""
    
    def __init__(self):
        self.html_normalizer = HTMLNormalizer()
        self.rss_normalizer = RSSNormalizer()
        self.json_normalizer = JSONNormalizer()
    
    async def normalize(self, parse_result: ParseResult) -> NormalizedData:
        """Normalize content using appropriate normalizer."""
        parser_type = parse_result.parser_type.lower()
        
        if "json" in parser_type:
            return await self.json_normalizer.normalize(parse_result)
        elif "rss" in parser_type:
            return await self.rss_normalizer.normalize(parse_result)
        else:
            return await self.html_normalizer.normalize(parse_result)