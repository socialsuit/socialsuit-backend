from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel

from app.models.models import User
from app.db.session import get_session
from app.core.security import get_current_user
from app.services.points import get_leaderboard
from app.services.leaderboard import top_n

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class LeaderboardEntry(BaseModel):
    id: str
    username: str
    total_points: int

    class Config:
        orm_mode = True


@router.get("/", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    limit: Optional[int] = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get the global leaderboard of users with the most points"""
    # Query users ordered by total_points
    result = await session.execute(
        select(User).order_by(User.total_points.desc()).limit(limit)
    )
    users = result.scalars().all()
    
    return users


@router.get("/campaign/{campaign_id}", response_model=List[LeaderboardEntry])
async def get_campaign_leaderboard(
    campaign_id: str,
    limit: Optional[int] = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get the leaderboard for a specific campaign"""
    # Use the points service to get campaign-specific leaderboard
    leaderboard = await get_leaderboard(campaign_id=campaign_id, limit=limit, session=session)
    
    return leaderboard


@router.get("/sparkr", response_model=List[LeaderboardEntry])
async def get_sparkr_leaderboard(
    platform: Optional[str] = Query(None, description="Filter by platform (twitter, instagram, etc.)"),
    limit: Optional[int] = Query(10, description="Maximum number of users to return", ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get the Sparkr leaderboard, optionally filtered by platform"""
    # Use the leaderboard service to get top users
    leaderboard = await top_n(platform=platform, n=limit)
    
    return leaderboard