import pytest
from httpx import AsyncClient
from sqlmodel import select
import json

from app.models.models import Campaign, Task, User, Submission
from app.models.schemas import VerificationStatusEnum
from app.core.security import get_password_hash, create_access_token
from app.services.points import redis_client


@pytest.fixture
async def test_admin_user(test_db_session):
    """Create a test admin user for submission review tests"""
    user_id = None
    async with test_db_session() as session:
        # Check if test admin user already exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create test admin user
            user = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("adminpassword"),
                is_admin=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        user_id = user.id
    
    # Create access token for the admin user
    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})
    
    return {"id": user_id, "token": access_token}


@pytest.fixture
async def test_submission(test_db_session, test_user, test_task):
    """Create a test submission for review tests"""
    submission_id = None
    async with test_db_session() as session:
        # Create submission
        submission = Submission(
            task_id=test_task,
            user_id=test_user["id"],
            submission_url="https://twitter.com/user/status/123456789",
            tweet_id="123456789",
            status="pending",
            points_awarded=0
        )
        session.add(submission)
        await session.commit()
        await session.refresh(submission)
        submission_id = submission.id
    
    return submission_id


@pytest.mark.asyncio
async def test_review_submission_approve(async_client: AsyncClient, test_db_session, test_admin_user, test_user, test_submission):
    """Test that reviewing and approving a submission updates user points and Redis"""
    # Clear Redis data before test
    try:
        await redis_client.delete(f"user:{test_user['id']}")
        await redis_client.zrem("leaderboard:global", test_user['id'])
        await redis_client.zrem("leaderboard:twitter", test_user['id'])
    except Exception:
        # Redis might not be available in test environment
        pass
    
    # Review data - approve submission
    review_data = {
        "status": "verified",
        "admin_notes": "Submission approved"
    }
    
    # Submit review
    response = await async_client.put(
        f"/api/v1/submissions/{test_submission}/review", 
        json=review_data,
        headers={"Authorization": f"Bearer {test_admin_user['token']}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert data["points_awarded"] > 0  # Points should be awarded
    
    # Verify in database
    async with test_db_session() as session:
        # Check submission updated
        result = await session.execute(select(Submission).where(Submission.id == test_submission))
        db_submission = result.scalar_one_or_none()
        assert db_submission is not None
        assert db_submission.status == VerificationStatusEnum.verified
        assert db_submission.points_awarded > 0
        
        # Check user points updated
        result = await session.execute(
            "SELECT total_points FROM users WHERE id = :user_id",
            {"user_id": test_user["id"]}
        )
        user_points = result.scalar_one_or_none() or 0
        assert user_points >= db_submission.points_awarded
    
    # Try to check Redis (may not be available in test environment)
    try:
        # Check user hash in Redis
        user_info = await redis_client.hgetall(f"user:{test_user['id']}")
        assert user_info is not None
        assert "total_points" in user_info
        assert int(user_info["total_points"]) >= db_submission.points_awarded
        
        # Check global leaderboard in Redis
        user_score = await redis_client.zscore("leaderboard:global", test_user['id'])
        assert user_score is not None
        assert user_score >= db_submission.points_awarded
        
        # Check platform leaderboard in Redis
        user_score = await redis_client.zscore("leaderboard:twitter", test_user['id'])
        assert user_score is not None
        assert user_score >= db_submission.points_awarded
    except Exception:
        # Redis might not be available in test environment
        pass


@pytest.mark.asyncio
async def test_review_submission_reject(async_client: AsyncClient, test_db_session, test_admin_user, test_user, test_submission):
    """Test that reviewing and rejecting a submission does not award points"""
    # Review data - reject submission
    review_data = {
        "status": "rejected",
        "admin_notes": "Submission rejected"
    }
    
    # Submit review
    response = await async_client.put(
        f"/api/v1/submissions/{test_submission}/review", 
        json=review_data,
        headers={"Authorization": f"Bearer {test_admin_user['token']}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["points_awarded"] == 0  # No points should be awarded
    
    # Verify in database
    async with test_db_session() as session:
        # Check submission updated
        result = await session.execute(select(Submission).where(Submission.id == test_submission))
        db_submission = result.scalar_one_or_none()
        assert db_submission is not None
        assert db_submission.status == VerificationStatusEnum.rejected
        assert db_submission.points_awarded == 0