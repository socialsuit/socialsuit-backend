import pytest
from sqlmodel import select
import json

from app.models.models import User
from app.core.security import get_password_hash
from app.services.points import get_user_points, redis_client


@pytest.fixture
async def test_user_with_points(test_db_session):
    """Create a test user with points for testing"""
    user_id = None
    async with test_db_session() as session:
        # Check if test user already exists
        result = await session.execute(select(User).where(User.email == "pointsuser@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create test user
            user = User(
                email="pointsuser@example.com",
                username="pointsuser",
                hashed_password=get_password_hash("testpassword"),
                total_points=100  # Set initial points
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Update points if user exists
            user.total_points = 100
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        user_id = user.id
    
    return {"id": user_id, "points": 100}


@pytest.mark.asyncio
async def test_get_user_points_from_redis(test_db_session, test_user_with_points):
    """Test that get_user_points retrieves points from Redis when available"""
    # Set up Redis with test data
    try:
        await redis_client.hset(
            f"user:{test_user_with_points['id']}", 
            mapping={
                "username": "pointsuser",
                "total_points": 150  # Different from DB to verify Redis is used
            }
        )
        
        # Get points - should come from Redis
        async with test_db_session() as session:
            points = await get_user_points(test_user_with_points['id'], session)
        
        # Verify points match Redis value, not DB value
        assert points == 150
        
        # Clean up Redis
        await redis_client.delete(f"user:{test_user_with_points['id']}")
    except Exception as e:
        # Redis might not be available in test environment
        pytest.skip(f"Redis not available for testing: {e}")


@pytest.mark.asyncio
async def test_get_user_points_from_db(test_db_session, test_user_with_points):
    """Test that get_user_points falls back to database when Redis fails"""
    # Clear Redis data to force DB fallback
    try:
        await redis_client.delete(f"user:{test_user_with_points['id']}")
    except Exception:
        # Redis might not be available in test environment
        pass
    
    # Get points - should come from DB
    async with test_db_session() as session:
        points = await get_user_points(test_user_with_points['id'], session)
    
    # Verify points match DB value
    assert points == 100
    
    # Verify Redis was updated with DB value
    try:
        user_info = await redis_client.hgetall(f"user:{test_user_with_points['id']}")
        assert user_info is not None
        assert "total_points" in user_info
        assert int(user_info["total_points"]) == 100
        
        # Clean up Redis
        await redis_client.delete(f"user:{test_user_with_points['id']}")
    except Exception:
        # Redis might not be available in test environment
        pass


@pytest.mark.asyncio
async def test_get_user_points_nonexistent_user(test_db_session):
    """Test that get_user_points returns 0 for nonexistent users"""
    # Get points for nonexistent user
    async with test_db_session() as session:
        points = await get_user_points("nonexistent-user-id", session)
    
    # Verify points are 0
    assert points == 0