"""Pydantic schemas for investor API responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProjectResponse(BaseModel):
    """Response schema for project information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    website: Optional[str] = None
    description: Optional[str] = None
    token_symbol: Optional[str] = None
    score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class InvestorPortfolioResponse(BaseModel):
    """Response schema for investor portfolio relationship."""
    model_config = ConfigDict(from_attributes=True)
    
    project_id: int
    first_invested_at: Optional[datetime] = None
    created_at: datetime
    project: Optional[ProjectResponse] = None


class InvestorResponse(BaseModel):
    """Response schema for investor information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    slug: str
    website: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    portfolios: Optional[List[InvestorPortfolioResponse]] = None


class InvestorListResponse(BaseModel):
    """Response schema for investor list with pagination."""
    investors: List[InvestorResponse]
    total: int
    skip: int
    limit: int


class InvestorCreateRequest(BaseModel):
    """Request schema for creating an investor."""
    name: str
    website: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None


class InvestorUpdateRequest(BaseModel):
    """Request schema for updating an investor."""
    name: Optional[str] = None
    website: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None