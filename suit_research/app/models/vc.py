"""MongoDB models for venture capital data storage."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId
from .crawl import PyObjectId


class Investor(BaseModel):
    """MongoDB model for storing investor/VC firm data."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., description="Name of the VC firm or investor")
    website: Optional[str] = Field(default=None, description="Official website URL")
    
    # Contact information
    email: Optional[str] = Field(default=None, description="Contact email")
    phone: Optional[str] = Field(default=None, description="Contact phone")
    address: Optional[str] = Field(default=None, description="Physical address")
    
    # Firm details
    description: Optional[str] = Field(default=None, description="Firm description")
    founded_year: Optional[int] = Field(default=None, description="Year the firm was founded")
    aum: Optional[float] = Field(default=None, description="Assets under management in USD")
    fund_size: Optional[float] = Field(default=None, description="Current fund size in USD")
    
    # Investment focus
    investment_stages: Optional[List[str]] = Field(default=None, description="Investment stages (seed, series_a, etc.)")
    sectors: Optional[List[str]] = Field(default=None, description="Investment sectors/industries")
    geographies: Optional[List[str]] = Field(default=None, description="Geographic focus areas")
    
    # Team information
    partners: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of partners and team members")
    
    # Portfolio information
    portfolio_companies: Optional[List[str]] = Field(default=None, description="List of portfolio company names")
    notable_investments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Notable investments with details")
    
    # Crawl metadata
    source_urls: List[str] = Field(default_factory=list, description="URLs where data was crawled from")
    crawled_at: datetime = Field(default_factory=datetime.utcnow, description="When the data was last crawled")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the record was last updated")
    
    # Data quality
    confidence_score: Optional[float] = Field(default=None, description="Confidence score for data quality (0-1)")
    verified: bool = Field(default=False, description="Whether the data has been manually verified")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Andreessen Horowitz",
                "website": "https://a16z.com",
                "description": "Venture capital firm focused on technology companies",
                "founded_year": 2009,
                "aum": 35000000000,
                "investment_stages": ["seed", "series_a", "series_b", "growth"],
                "sectors": ["fintech", "crypto", "ai", "enterprise"],
                "geographies": ["united_states", "global"],
                "source_urls": ["https://a16z.com/portfolio", "https://a16z.com/about"]
            }
        }


class FundingRound(BaseModel):
    """MongoDB model for storing funding round data (staging table)."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Company information
    company_name: str = Field(..., description="Name of the company that received funding")
    company_website: Optional[str] = Field(default=None, description="Company website URL")
    company_description: Optional[str] = Field(default=None, description="Company description")
    
    # Funding details
    round_type: Optional[str] = Field(default=None, description="Type of funding round (seed, series_a, etc.)")
    amount: Optional[float] = Field(default=None, description="Funding amount in USD")
    currency: str = Field(default="USD", description="Currency of the funding amount")
    valuation: Optional[float] = Field(default=None, description="Company valuation in USD")
    
    # Date information
    announced_date: Optional[datetime] = Field(default=None, description="Date the funding was announced")
    closed_date: Optional[datetime] = Field(default=None, description="Date the funding round closed")
    
    # Investors
    lead_investors: Optional[List[str]] = Field(default=None, description="Lead investor names")
    participating_investors: Optional[List[str]] = Field(default=None, description="All participating investor names")
    investor_ids: Optional[List[PyObjectId]] = Field(default=None, description="ObjectIds of investors in our database")
    
    # Company details
    sector: Optional[str] = Field(default=None, description="Company sector/industry")
    stage: Optional[str] = Field(default=None, description="Company stage (startup, growth, etc.)")
    location: Optional[str] = Field(default=None, description="Company location")
    employee_count: Optional[int] = Field(default=None, description="Number of employees")
    
    # Use of funds
    use_of_funds: Optional[str] = Field(default=None, description="Stated use of the funding")
    
    # Crawl metadata
    source_url: str = Field(..., description="URL where this funding information was found")
    source_type: str = Field(default="press_release", description="Type of source (press_release, portfolio_page, news)")
    crawled_at: datetime = Field(default_factory=datetime.utcnow, description="When the data was crawled")
    
    # Processing status
    processed: bool = Field(default=False, description="Whether this record has been processed into final tables")
    processed_at: Optional[datetime] = Field(default=None, description="When the record was processed")
    
    # Data quality
    confidence_score: Optional[float] = Field(default=None, description="Confidence score for extracted data (0-1)")
    extraction_method: str = Field(default="html_parsing", description="Method used to extract the data")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "company_name": "Stripe",
                "company_website": "https://stripe.com",
                "round_type": "series_h",
                "amount": 600000000,
                "valuation": 95000000000,
                "announced_date": "2021-03-14T00:00:00Z",
                "lead_investors": ["Andreessen Horowitz", "General Catalyst"],
                "participating_investors": ["Andreessen Horowitz", "General Catalyst", "Sequoia Capital"],
                "sector": "fintech",
                "location": "San Francisco, CA",
                "source_url": "https://a16z.com/portfolio/stripe",
                "source_type": "portfolio_page"
            }
        }


class VCCrawlJob(BaseModel):
    """MongoDB model for tracking VC crawl jobs."""
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Job details
    job_name: str = Field(..., description="Name/identifier for this crawl job")
    vc_firm_name: str = Field(..., description="Name of the VC firm being crawled")
    target_urls: List[str] = Field(..., description="List of URLs to crawl")
    
    # Job configuration
    crawl_config: Dict[str, Any] = Field(default_factory=dict, description="Crawler configuration")
    
    # Status tracking
    status: str = Field(default="pending", description="Job status (pending, running, completed, failed)")
    started_at: Optional[datetime] = Field(default=None, description="When the job started")
    completed_at: Optional[datetime] = Field(default=None, description="When the job completed")
    
    # Results
    urls_crawled: int = Field(default=0, description="Number of URLs successfully crawled")
    urls_failed: int = Field(default=0, description="Number of URLs that failed")
    investors_found: int = Field(default=0, description="Number of investor records created")
    funding_rounds_found: int = Field(default=0, description="Number of funding rounds found")
    
    # Error tracking
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of errors encountered")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the job was created")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}