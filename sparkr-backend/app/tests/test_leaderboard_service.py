import pytest
import fakeredis.aioredis
from unittest import mock

from app.services.leaderboard import add_points, top_n, redis_client
from app.models.schemas import PlatformEnum


@pytest.fixture
def mock_redis():
    """Create a mock Redis client using fakeredis"""
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return fake_redis


@pytest.fixture
async def setup_leaderboard_data(mock_redis):
    """Set up test data in the fake Redis instance"""
    # Add users to global leaderboard
    await mock_redis.zadd("leaderboard:global", {
        "user1": 100,
        "user2": 200,
        "user3": 150,
        "user4": 75
    })
    
    # Add users to platform-specific leaderboards
    await mock_redis.zadd("leaderboard:twitter", {
        "user1": 50,
        "user2": 120,
        "user3": 80
    })
    
    await mock_redis.zadd("leaderboard:instagram", {
        "user1": 30,
        "user2": 60,
        "user3": 45,
        "user4": 75
    })
    
    # Store user info
    users = [
        {"id": "user1", "username": "testuser1", "total_points": 100},
        {"id": "user2", "username": "testuser2", "total_points": 200},
        {"id": "user3", "username": "testuser3", "total_points": 150},
        {"id": "user4", "username": "testuser4", "total_points": 75}
    ]
    
    for user in users:
        await mock_redis.hset(f"user:{user['id']}", mapping={
            "username": user["username"],
            "total_points": user["total_points"]
        })


@pytest.mark.asyncio
async def test_add_points(mock_redis):
    """Test adding points to a user"""
    with mock.patch('app.services.leaderboard.redis_client', mock_redis):
        # Add points to a user
        result = await add_points("user1", "twitter", 50)
        
        # Check that points were added successfully
        assert result is True
        
        # Check that points were added to global leaderboard
        global_score = await mock_redis.zscore("leaderboard:global", "user1")
        assert global_score == 50
        
        # Check that points were added to platform leaderboard
        platform_score = await mock_redis.zscore("leaderboard:twitter", "user1")
        assert platform_score == 50


@pytest.mark.asyncio
async def test_top_n_global(mock_redis, setup_leaderboard_data):
    """Test getting top users from global leaderboard"""
    with mock.patch('app.services.leaderboard.redis_client', mock_redis):
        # Get top 3 users
        leaderboard = await top_n(n=3)
        
        # Check that we got the expected number of users
        assert len(leaderboard) == 3
        
        # Check that users are ordered by score (descending)
        assert leaderboard[0]["id"] == "user2"  # 200 points
        assert leaderboard[1]["id"] == "user3"  # 150 points
        assert leaderboard[2]["id"] == "user1"  # 100 points
        
        # Check that user info is included
        assert leaderboard[0]["username"] == "testuser2"
        assert leaderboard[0]["total_points"] == 200


@pytest.mark.asyncio
async def test_top_n_platform(mock_redis, setup_leaderboard_data):
    """Test getting top users from platform-specific leaderboard"""
    with mock.patch('app.services.leaderboard.redis_client', mock_redis):
        # Get top 2 users for Twitter
        leaderboard = await top_n(platform="twitter", n=2)
        
        # Check that we got the expected number of users
        assert len(leaderboard) == 2
        
        # Check that users are ordered by score (descending)
        assert leaderboard[0]["id"] == "user2"  # 120 points
        assert leaderboard[1]["id"] == "user3"  # 80 points
        
        # Get top 2 users for Instagram
        leaderboard = await top_n(platform="instagram", n=2)
        
        # Check that we got the expected number of users
        assert len(leaderboard) == 2
        
        # Check that users are ordered by score (descending)
        assert leaderboard[0]["id"] == "user4"  # 75 points
        assert leaderboard[1]["id"] == "user2"  # 60 points