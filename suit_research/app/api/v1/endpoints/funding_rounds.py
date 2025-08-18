"""Funding round-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
import math

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.funding import FundingRound
from app.models.project import Project
from app.models.user import User
from app.api.schemas.project import (
    FundingRoundResponse,
    FundingRoundListResponse,
    FundingRoundCreateRequest,
    FundingRoundUpdateRequest
)

router = APIRouter()


@router.get("/", response_model=FundingRoundListResponse)
async def get_funding_rounds(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    round_type: Optional[str] = Query(None, description="Filter by round type (seed, series_a, etc.)"),
    min_amount: Optional[float] = Query(None, description="Minimum funding amount in USD"),
    max_amount: Optional[float] = Query(None, description="Maximum funding amount in USD"),
    from_date: Optional[datetime] = Query(None, description="Filter funding rounds from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter funding rounds to this date"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of funding rounds with pagination and filtering.
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of items per page (max 100)
    - **project_id**: Filter by specific project
    - **round_type**: Filter by funding round type
    - **min_amount**: Minimum funding amount in USD
    - **max_amount**: Maximum funding amount in USD
    - **from_date**: Filter funding rounds from this date
    - **to_date**: Filter funding rounds to this date
    """
    # Build query with project relationship
    query = select(FundingRound).options(selectinload(FundingRound.project))
    count_query = select(func.count(FundingRound.id))
    
    # Apply filters
    if project_id:
        project_filter = FundingRound.project_id == project_id
        query = query.where(project_filter)
        count_query = count_query.where(project_filter)
    
    if round_type:
        round_filter = FundingRound.round_type.ilike(f"%{round_type}%")
        query = query.where(round_filter)
        count_query = count_query.where(round_filter)
    
    if min_amount is not None:
        min_filter = FundingRound.amount_usd >= min_amount
        query = query.where(min_filter)
        count_query = count_query.where(min_filter)
    
    if max_amount is not None:
        max_filter = FundingRound.amount_usd <= max_amount
        query = query.where(max_filter)
        count_query = count_query.where(max_filter)
    
    if from_date:
        from_filter = FundingRound.announced_at >= from_date
        query = query.where(from_filter)
        count_query = count_query.where(from_filter)
    
    if to_date:
        to_filter = FundingRound.announced_at <= to_date
        query = query.where(to_filter)
        count_query = count_query.where(to_filter)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(FundingRound.announced_at.desc().nulls_last())
    
    # Execute query
    result = await db.execute(query)
    funding_rounds = result.scalars().all()
    
    # Calculate pagination info
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    has_next = page < total_pages
    has_prev = page > 1
    
    return FundingRoundListResponse(
        items=[FundingRoundResponse.model_validate(funding_round) for funding_round in funding_rounds],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{funding_round_id}", response_model=FundingRoundResponse)
async def get_funding_round(
    funding_round_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific funding round by ID.
    
    - **funding_round_id**: The ID of the funding round to retrieve
    """
    query = select(FundingRound).options(selectinload(FundingRound.project)).where(FundingRound.id == funding_round_id)
    result = await db.execute(query)
    funding_round = result.scalar_one_or_none()
    
    if not funding_round:
        raise HTTPException(status_code=404, detail="Funding round not found")
    
    return FundingRoundResponse.model_validate(funding_round)


@router.post("/", response_model=FundingRoundResponse, status_code=201)
async def create_funding_round(
    funding_round_data: FundingRoundCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new funding round.
    
    Requires authentication.
    """
    # Verify project exists
    project_query = select(Project).where(Project.id == funding_round_data.project_id)
    project_result = await db.execute(project_query)
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Project not found")
    
    # Create new funding round
    funding_round = FundingRound(**funding_round_data.model_dump())
    db.add(funding_round)
    await db.commit()
    await db.refresh(funding_round)
    
    # Load project relationship
    await db.refresh(funding_round, ['project'])
    
    return FundingRoundResponse.model_validate(funding_round)


@router.put("/{funding_round_id}", response_model=FundingRoundResponse)
async def update_funding_round(
    funding_round_id: int,
    funding_round_data: FundingRoundUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing funding round.
    
    Requires authentication.
    """
    # Get existing funding round
    query = select(FundingRound).where(FundingRound.id == funding_round_id)
    result = await db.execute(query)
    funding_round = result.scalar_one_or_none()
    
    if not funding_round:
        raise HTTPException(status_code=404, detail="Funding round not found")
    
    # Verify project exists if being updated
    if funding_round_data.project_id and funding_round_data.project_id != funding_round.project_id:
        project_query = select(Project).where(Project.id == funding_round_data.project_id)
        project_result = await db.execute(project_query)
        if not project_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Project not found")
    
    # Update funding round
    update_data = funding_round_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(funding_round, field, value)
    
    await db.commit()
    await db.refresh(funding_round)
    
    # Load project relationship
    await db.refresh(funding_round, ['project'])
    
    return FundingRoundResponse.model_validate(funding_round)


@router.delete("/{funding_round_id}", status_code=204)
async def delete_funding_round(
    funding_round_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a funding round.
    
    Requires authentication.
    """
    # Get existing funding round
    query = select(FundingRound).where(FundingRound.id == funding_round_id)
    result = await db.execute(query)
    funding_round = result.scalar_one_or_none()
    
    if not funding_round:
        raise HTTPException(status_code=404, detail="Funding round not found")
    
    # Delete funding round
    await db.delete(funding_round)
    await db.commit()