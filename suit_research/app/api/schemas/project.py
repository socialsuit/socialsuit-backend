"""Pydantic schemas for project-related API endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProjectCategory(str, Enum):
    """Valid project categories."""
    DEFI = "defi"
    LAYER_1 = "layer_1"
    LAYER_2 = "layer_2"
    NFT = "nft"
    GAMING = "gaming"
    INFRASTRUCTURE = "infrastructure"
    AI = "ai"
    DEX = "dex"
    WALLET = "wallet"
    TOOLING = "tooling"


class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., description="Project name", example="Uniswap")
    slug: str = Field(..., description="Project slug (URL-friendly identifier)", example="uniswap")
    website: Optional[str] = Field(None, description="Project website URL", example="https://uniswap.org")
    description: Optional[str] = Field(None, description="Project description", example="A decentralized exchange protocol")
    token_symbol: Optional[str] = Field(None, description="Token symbol", example="UNI")
    score: Optional[Decimal] = Field(None, description="Project score", example=95.5)
    category: Optional[ProjectCategory] = Field(None, description="Project category", example=ProjectCategory.DEX)
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ProjectCreateRequest(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdateRequest(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, description="Project name", example="Uniswap V3")
    slug: Optional[str] = Field(None, description="Project slug", example="uniswap-v3")
    website: Optional[str] = Field(None, description="Project website URL", example="https://uniswap.org")
    description: Optional[str] = Field(None, description="Project description", example="Advanced AMM protocol")
    token_symbol: Optional[str] = Field(None, description="Token symbol", example="UNI")
    score: Optional[Decimal] = Field(None, description="Project score", example=98.0)
    category: Optional[ProjectCategory] = Field(None, description="Project category", example=ProjectCategory.DEX)
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ProjectResponse(ProjectBase):
    """Schema for project API responses."""
    id: int = Field(..., description="Project ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for project list API responses."""
    items: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class FundingRoundBase(BaseModel):
    """Base funding round schema."""
    project_id: int = Field(..., description="Project ID")
    round_type: str = Field(..., description="Type of funding round (seed, series_a, etc.)")
    amount_usd: Optional[Decimal] = Field(None, description="Funding amount in USD")
    currency: Optional[str] = Field(None, description="Currency code")
    announced_at: Optional[datetime] = Field(None, description="Announcement date")
    investors: Optional[List[Dict[str, Any]]] = Field(None, description="List of investors")
    source_url: Optional[str] = Field(None, description="Source URL")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FundingRoundCreateRequest(FundingRoundBase):
    """Schema for creating a new funding round."""
    pass


class FundingRoundUpdateRequest(BaseModel):
    """Schema for updating a funding round."""
    project_id: Optional[int] = Field(None, description="Project ID")
    round_type: Optional[str] = Field(None, description="Type of funding round")
    amount_usd: Optional[Decimal] = Field(None, description="Funding amount in USD")
    currency: Optional[str] = Field(None, description="Currency code")
    announced_at: Optional[datetime] = Field(None, description="Announcement date")
    investors: Optional[List[Dict[str, Any]]] = Field(None, description="List of investors")
    source_url: Optional[str] = Field(None, description="Source URL")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class FundingRoundResponse(FundingRoundBase):
    """Schema for funding round API responses."""
    id: int = Field(..., description="Funding round ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class FundingRoundListResponse(BaseModel):
    """Schema for funding round list API responses."""
    items: List[FundingRoundResponse] = Field(..., description="List of funding rounds")
    total: int = Field(..., description="Total number of funding rounds")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class WebhookPayload(BaseModel):
    """Schema for webhook payloads."""
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(..., description="Event timestamp")
    source: str = Field(..., description="Event source")


class WebhookResponse(BaseModel):
    """Schema for webhook responses."""
    success: bool = Field(..., description="Whether webhook was processed successfully")
    message: str = Field(..., description="Response message")
    webhook_id: Optional[str] = Field(None, description="Webhook ID for tracking")