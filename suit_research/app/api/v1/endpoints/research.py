"""
Research-related endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.models.research import Research
from app.services.research_service import ResearchService

router = APIRouter()


@router.get("/")
async def get_research_list(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of research items.
    """
    service = ResearchService(db)
    research_items = await service.get_research_list(skip=skip, limit=limit)
    return research_items


@router.get("/{research_id}")
async def get_research(
    research_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific research item by ID.
    """
    service = ResearchService(db)
    research = await service.get_research_by_id(research_id)
    if not research:
        raise HTTPException(status_code=404, detail="Research not found")
    return research


@router.post("/")
async def create_research(
    research_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new research item.
    """
    service = ResearchService(db)
    research = await service.create_research(research_data)
    return research