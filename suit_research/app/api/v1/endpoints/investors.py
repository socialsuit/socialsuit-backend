"""Investor API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.investor_service import InvestorService
from app.api.schemas.investor import InvestorResponse, InvestorListResponse, ProjectResponse

router = APIRouter()


@router.get("/", response_model=InvestorListResponse)
async def get_investors(
    skip: int = Query(0, ge=0, description="Number of investors to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of investors to return"),
    search: Optional[str] = Query(None, description="Search investors by name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of investors.
    
    - **skip**: Number of investors to skip (for pagination)
    - **limit**: Maximum number of investors to return
    - **search**: Optional search term to filter investors by name
    """
    service = InvestorService(db)
    investors = await service.get_investors(skip=skip, limit=limit, search=search)
    
    return InvestorListResponse(
        investors=[InvestorResponse.from_orm(investor) for investor in investors],
        total=len(investors),
        skip=skip,
        limit=limit
    )


@router.get("/{investor_id}", response_model=InvestorResponse)
async def get_investor(
    investor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get investor by ID.
    
    - **investor_id**: The ID of the investor to retrieve
    """
    service = InvestorService(db)
    investor = await service.get_investor_by_id(investor_id)
    
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    return InvestorResponse.from_orm(investor)


@router.get("/{investor_id}/portfolio", response_model=List[ProjectResponse])
async def get_investor_portfolio(
    investor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get investor's portfolio (list of projects they've invested in).
    
    - **investor_id**: The ID of the investor
    """
    service = InvestorService(db)
    
    # First check if investor exists
    investor = await service.get_investor_by_id(investor_id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    # Get portfolio projects
    projects = await service.get_investor_portfolio(investor_id)
    
    return [ProjectResponse.from_orm(project) for project in projects]


@router.post("/link-funding/{funding_round_id}")
async def link_funding_to_investors(
    funding_round_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Link a funding round to investor profiles and update portfolios.
    
    This endpoint processes a funding round and:
    1. Parses investor information from the funding data
    2. Creates new investors or matches existing ones using fuzzy matching
    3. Updates investor portfolios with the new investment
    
    - **funding_round_id**: The ID of the funding round to process
    """
    from app.models.funding import FundingRound
    from sqlalchemy import select
    
    # Get the funding round
    query = select(FundingRound).where(FundingRound.id == funding_round_id)
    result = await db.execute(query)
    funding_round = result.scalar_one_or_none()
    
    if not funding_round:
        raise HTTPException(status_code=404, detail="Funding round not found")
    
    service = InvestorService(db)
    await service.link_funding_to_investors(funding_round)
    
    return {"message": "Funding round successfully linked to investors", "funding_round_id": funding_round_id}