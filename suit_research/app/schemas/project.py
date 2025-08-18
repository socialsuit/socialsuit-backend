"""Project Pydantic schemas."""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base Project schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    slug: str = Field(..., min_length=1, max_length=255, description="Project slug (URL-friendly identifier)")
    website: Optional[str] = Field(None, max_length=500, description="Project website URL")
    description: Optional[str] = Field(None, description="Project description")
    token_symbol: Optional[str] = Field(None, max_length=20, description="Token symbol")
    category: Optional[str] = Field(
        None, 
        description="Project category",
        examples=["defi", "layer_1", "layer_2", "nft", "gaming", "infrastructure", "ai", "dex", "wallet", "tooling"]
    )
    score: Optional[Decimal] = Field(None, ge=0, le=100, description="Project score (0-100)")
    meta_data: Optional[dict] = Field(None, description="Additional metadata")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="Project slug")
    website: Optional[str] = Field(None, max_length=500, description="Project website URL")
    description: Optional[str] = Field(None, description="Project description")
    token_symbol: Optional[str] = Field(None, max_length=20, description="Token symbol")
    category: Optional[str] = Field(
        None, 
        description="Project category",
        examples=["defi", "layer_1", "layer_2", "nft", "gaming", "infrastructure", "ai", "dex", "wallet", "tooling"]
    )
    score: Optional[Decimal] = Field(None, ge=0, le=100, description="Project score (0-100)")
    meta_data: Optional[dict] = Field(None, description="Additional metadata")


class ProjectInDBBase(ProjectBase):
    """Base schema for project data from database."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class Project(ProjectInDBBase):
    """Schema for project data returned to client."""
    pass


class ProjectInDB(ProjectInDBBase):
    """Schema for project data stored in database."""
    pass


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response."""
    items: List[Project]
    total: int
    page: int
    size: int
    pages: int


class ProjectCategoryFilter(BaseModel):
    """Schema for project category filtering."""
    category: Optional[str] = Field(
        None,
        description="Filter projects by category",
        examples=["defi", "layer_1", "layer_2", "nft", "gaming", "infrastructure", "ai", "dex", "wallet", "tooling"]
    )


# Category constants for validation and documentation
PROJECT_CATEGORIES = [
    "defi",
    "layer_1", 
    "layer_2",
    "nft",
    "gaming",
    "infrastructure",
    "ai",
    "dex",
    "wallet",
    "tooling"
]


class ProjectCategoryStats(BaseModel):
    """Schema for project category statistics."""
    category: str
    count: int
    percentage: float