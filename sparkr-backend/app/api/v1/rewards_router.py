from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from datetime import datetime

from app.models.models import User
from app.models.reward import Reward
from app.db.session import get_session
from app.core.security import get_current_user

router = APIRouter(prefix="/rewards", tags=["rewards"])


class RewardResponse(BaseModel):
    id: str
    submission_id: str
    points: int
    created_at: datetime

    class Config:
        orm_mode = True


class UserRewardsResponse(BaseModel):
    user_id: str
    username: str
    total_points: int
    rewards: List[RewardResponse]

    class Config:
        orm_mode = True


@router.get("/", response_model=UserRewardsResponse)
async def get_user_rewards(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all rewards for the current user"""
    # Query rewards for the current user
    result = await session.execute(
        select(Reward).where(Reward.user_id == current_user.id)
    )
    rewards = result.scalars().all()
    
    # Create response
    response = {
        "user_id": current_user.id,
        "username": current_user.username,
        "total_points": current_user.total_points,
        "rewards": rewards
    }
    
    return response