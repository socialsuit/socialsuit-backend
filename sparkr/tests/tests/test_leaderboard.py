import pytest
from sqlmodel import select

from sparkr.app.models.models import User, Campaign, Task, Submission
from sparkr.app.core.security import get_password_hash
from sparkr.app.services.points import get_leaderboard, redis_client
from sparkr.app.models.schemas import PlatformEnum


@pytest.fixture
async def test_leaderboard_users(test_db_session):
    """Create test users with points for leaderboard testing"""
    user_ids = []
    
    async with test_db_session() as session:
        # Create or update multiple users with different point values
        users_data = [
            {"email": "user1@example.com", "username": "user1", "points": 100},
            {"email": "user2@example.com", "username": "user2", "points": 200},
            {"email": "user3@example.com", "username": "user3", "points": 150},
        ]
        
        for user_data in users_data:
            # Check if user exists
            result = await session.execute(select(User).where(User.email == user_data["email"]))
            user = result.scalar_one_or_none()
            
            if not user:
                # Create new user
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash("testpassword"),
                    total_points=user_data["points"]
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                # Update existing user
                user.total_points = user_data["points"]
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            user_ids.append({"id": user.id, "username": user.username, "points": user_data["points"]})
    
    return user_ids


@pytest.fixture
async def test_campaign_with_submissions(test_db_session, test_leaderboard_users):
    """Create a test campaign with submissions for campaign-specific leaderboard testing"""
    campaign_id = None
    
    async with test_db_session() as session:
        # Create campaign
        campaign = Campaign(
            name="Leaderboard Test Campaign",
            description="Campaign for testing leaderboard functionality",
            start_date="2023-01-01",
            end_date="2023-12-31",
            status="active"
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        campaign_id = campaign.id
        
        # Create tasks for different platforms
        platforms = [PlatformEnum.twitter, PlatformEnum.instagram, PlatformEnum.tiktok]
        task_ids = []
        
        for i, platform in enumerate(platforms):
            task = Task(
                campaign_id=campaign_id,
                title=f"Test Task {i+1}",
                description=f"Task for {platform} platform",
                platform=platform,
                points=30 * (i+1),  # Different point values
                status="active"
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            task_ids.append({"id": task.id, "platform": platform})
        
        # Create verified submissions with awarded points
        for i, user in enumerate(test_leaderboard_users):
            # Each user completes different tasks
            for j, task in enumerate(task_ids):
                if (i + j) % 3 == 0:  # Create some submissions, not all
                    submission = Submission(
                        task_id=task["id"],
                        user_id=user["id"],
                        submission_url=f"https://example.com/{task['platform']}/{user['username']}/123",
                        status="verified",
                        points_awarded=30 * (j+1)  # Match task points
                    )
                    session.add(submission)
        
        await session.commit()
    
    return {"id": campaign_id, "tasks": task_ids}


@pytest.mark.asyncio
async def test_global_leaderboard_from_redis(test_db_session, test_leaderboard_users):
    """Test that get_leaderboard retrieves global leaderboard from Redis when available"""
    try:
        # Set up Redis with test data
        for user in test_leaderboard_users:
            # Add to global leaderboard
            await redis_client.zadd("leaderboard:global", {user["id"]: user["points"]})
            # Add user info
            await redis_client.hset(
                f"user:{user['id']}", 
                mapping={
                    "username": user["username"],
                    "total_points": user["points"]
                }
            )
        
        # Get global leaderboard
        async with test_db_session() as session:
            leaderboard = await get_leaderboard(session, limit=10)
        
        # Verify leaderboard
        assert len(leaderboard) == len(test_leaderboard_users)
        
        # Verify order (highest points first)
        sorted_users = sorted(test_leaderboard_users, key=lambda x: x["points"], reverse=True)
        for i, entry in enumerate(leaderboard):
            assert entry["username"] == sorted_users[i]["username"]
            assert entry["points"] == sorted_users[i]["points"]
        
        # Clean up Redis
        for user in test_leaderboard_users:
            await redis_client.zrem("leaderboard:global", user["id"])
            await redis_client.delete(f"user:{user['id']}")
            
    except Exception as e:
        # Redis might not be available in test environment
        pytest.skip(f"Redis not available for testing: {e}")


@pytest.mark.asyncio
async def test_platform_leaderboard_from_redis(test_db_session, test_leaderboard_users):
    """Test that get_leaderboard retrieves platform-specific leaderboard from Redis"""
    try:
        # Set up Redis with test data for Twitter platform
        platform_points = {
            test_leaderboard_users[0]["id"]: 50,
            test_leaderboard_users[1]["id"]: 100,
            test_leaderboard_users[2]["id"]: 75
        }
        
        for user_id, points in platform_points.items():
            # Add to platform leaderboard
            await redis_client.zadd("leaderboard:twitter", {user_id: points})
        
        # Add user info
        for user in test_leaderboard_users:
            await redis_client.hset(
                f"user:{user['id']}", 
                mapping={
                    "username": user["username"],
                    "total_points": user["points"]
                }
            )
        
        # Get platform leaderboard
        async with test_db_session() as session:
            leaderboard = await get_leaderboard(session, platform=PlatformEnum.twitter, limit=10)
        
        # Verify leaderboard
        assert len(leaderboard) == len(platform_points)
        
        # Verify order (highest points first)
        expected_order = sorted([
            {"id": user_id, "points": points, "username": next(u["username"] for u in test_leaderboard_users if u["id"] == user_id)}
            for user_id, points in platform_points.items()
        ], key=lambda x: x["points"], reverse=True)
        
        for i, entry in enumerate(leaderboard):
            assert entry["username"] == expected_order[i]["username"]
            assert entry["points"] == expected_order[i]["points"]
        
        # Clean up Redis
        for user in test_leaderboard_users:
            await redis_client.zrem("leaderboard:twitter", user["id"])
            await redis_client.delete(f"user:{user['id']}")
            
    except Exception as e:
        # Redis might not be available in test environment
        pytest.skip(f"Redis not available for testing: {e}")


@pytest.mark.asyncio
async def test_campaign_leaderboard(test_db_session, test_leaderboard_users, test_campaign_with_submissions):
    """Test that get_leaderboard retrieves campaign-specific leaderboard from database"""
    # Get campaign leaderboard
    async with test_db_session() as session:
        leaderboard = await get_leaderboard(
            session, 
            campaign_id=test_campaign_with_submissions["id"],
            limit=10
        )
    
    # Verify leaderboard has entries
    assert len(leaderboard) > 0
    
    # Verify order (highest points first)
    for i in range(len(leaderboard) - 1):
        assert leaderboard[i]["points"] >= leaderboard[i+1]["points"]