"""Watchlist API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.alert import Watchlist
from app.models.user import User
from app.models.project import Project
from app.api.schemas.alert import (
    WatchlistCreateRequest,
    WatchlistUpdateRequest,
    WatchlistResponse,
    WatchlistListResponse
)

router = APIRouter()


# Mock function to get current user - replace with actual auth
async def get_current_user() -> int:
    """Mock function to get current user ID. Replace with actual authentication."""
    return 1  # Mock user ID


@router.get("/", response_model=WatchlistListResponse)
async def get_user_watchlist(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Get user's watchlist with pagination.
    
    - **skip**: Number of items to skip (for pagination)
    - **limit**: Maximum number of items to return
    """
    query = (
        select(Watchlist)
        .where(Watchlist.user_id == current_user_id)
        .options(selectinload(Watchlist.project))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    watchlist_items = result.scalars().all()
    
    # Get total count for pagination
    count_query = select(Watchlist).where(Watchlist.user_id == current_user_id)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return WatchlistListResponse(
        watchlist=[WatchlistResponse.model_validate(item) for item in watchlist_items],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist_item(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Get watchlist item by ID.
    
    - **watchlist_id**: The ID of the watchlist item to retrieve
    """
    query = (
        select(Watchlist)
        .where(and_(Watchlist.id == watchlist_id, Watchlist.user_id == current_user_id))
        .options(selectinload(Watchlist.project))
    )
    result = await db.execute(query)
    watchlist_item = result.scalar_one_or_none()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    return WatchlistResponse.model_validate(watchlist_item)


@router.post("/", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist_data: WatchlistCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Add a project to user's watchlist.
    
    - **project_id**: The ID of the project to add to watchlist
    - **notes**: Optional notes about the project
    """
    # Verify project exists
    project_query = select(Project).where(Project.id == watchlist_data.project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project is already in user's watchlist
    existing_query = select(Watchlist).where(
        and_(
            Watchlist.user_id == current_user_id,
            Watchlist.project_id == watchlist_data.project_id
        )
    )
    existing_result = await db.execute(existing_query)
    existing_item = existing_result.scalar_one_or_none()
    
    if existing_item:
        raise HTTPException(
            status_code=400, 
            detail="Project is already in your watchlist"
        )
    
    # Create new watchlist item
    watchlist_item = Watchlist(
        user_id=current_user_id,
        project_id=watchlist_data.project_id,
        notes=watchlist_data.notes
    )
    
    db.add(watchlist_item)
    await db.commit()
    await db.refresh(watchlist_item)
    
    return WatchlistResponse.model_validate(watchlist_item)


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_item(
    watchlist_id: int,
    watchlist_data: WatchlistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Update a watchlist item.
    
    - **watchlist_id**: The ID of the watchlist item to update
    - **notes**: Optional new notes about the project
    """
    query = select(Watchlist).where(
        and_(Watchlist.id == watchlist_id, Watchlist.user_id == current_user_id)
    )
    result = await db.execute(query)
    watchlist_item = result.scalar_one_or_none()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    # Update notes if provided
    if watchlist_data.notes is not None:
        watchlist_item.notes = watchlist_data.notes
    
    await db.commit()
    await db.refresh(watchlist_item)
    
    return WatchlistResponse.model_validate(watchlist_item)


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Remove a project from user's watchlist.
    
    - **watchlist_id**: The ID of the watchlist item to remove
    """
    query = select(Watchlist).where(
        and_(Watchlist.id == watchlist_id, Watchlist.user_id == current_user_id)
    )
    result = await db.execute(query)
    watchlist_item = result.scalar_one_or_none()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    await db.delete(watchlist_item)
    await db.commit()
    
    return {"message": "Project removed from watchlist", "watchlist_id": watchlist_id}


@router.delete("/project/{project_id}")
async def remove_project_from_watchlist(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Remove a project from user's watchlist by project ID.
    
    - **project_id**: The ID of the project to remove from watchlist
    """
    query = select(Watchlist).where(
        and_(
            Watchlist.user_id == current_user_id,
            Watchlist.project_id == project_id
        )
    )
    result = await db.execute(query)
    watchlist_item = result.scalar_one_or_none()
    
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Project not found in watchlist")
    
    await db.delete(watchlist_item)
    await db.commit()
    
    return {"message": "Project removed from watchlist", "project_id": project_id}