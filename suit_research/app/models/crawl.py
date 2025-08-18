"""
MongoDB models for raw crawl data storage.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        field_schema.update(type="string")
        return field_schema


class RawCrawl(BaseModel):
    """MongoDB model for storing raw crawl data."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    raw_html: str = Field(..., description="Raw HTML content from the crawl")
    source: str = Field(..., description="Source URL or identifier")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When the data was scraped")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the crawl")
    
    # Processing status
    processed: bool = Field(default=False, description="Whether this crawl has been processed")
    processed_at: Optional[datetime] = Field(default=None, description="When the crawl was processed")
    
    # Content analysis
    content_type: Optional[str] = Field(default=None, description="Type of content (news, blog, etc.)")
    language: Optional[str] = Field(default=None, description="Detected language")
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if crawl failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "raw_html": "<html><body>Sample content</body></html>",
                "source": "https://example.com/news/article-1",
                "scraped_at": "2024-01-15T10:30:00Z",
                "metadata": {
                    "user_agent": "Mozilla/5.0...",
                    "status_code": 200,
                    "headers": {"content-type": "text/html"}
                },
                "processed": False,
                "content_type": "news",
                "language": "en"
            }
        }


class CrawlStats(BaseModel):
    """MongoDB model for crawl statistics and monitoring."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    date: datetime = Field(..., description="Date for these statistics")
    source: str = Field(..., description="Source identifier")
    
    # Crawl metrics
    total_crawls: int = Field(default=0, description="Total number of crawls")
    successful_crawls: int = Field(default=0, description="Number of successful crawls")
    failed_crawls: int = Field(default=0, description="Number of failed crawls")
    
    # Performance metrics
    avg_response_time: Optional[float] = Field(default=None, description="Average response time in seconds")
    total_data_size: Optional[int] = Field(default=None, description="Total data size in bytes")
    
    # Content metrics
    content_types: Optional[Dict[str, int]] = Field(default=None, description="Count by content type")
    languages: Optional[Dict[str, int]] = Field(default=None, description="Count by language")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}