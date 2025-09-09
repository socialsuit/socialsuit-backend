import redis.asyncio as redis
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from sparkr.app.core.config import settings

# Create Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def add_points(user_id: str, platform: str, points: int, session: AsyncSession = None) -> bool:
    """
    Add points to a user's score and update Redis leaderboard
    
    Args:
        user_id: The ID of the user to add points to
        platform: The platform the points are from (twitter, instagram, etc.)
        points: The number of points to add
        session: Optional database session for updating user_points in DB
        
    Returns:
        bool: True if points were added successfully, False otherwise
    """
    try:
        # Update Redis leaderboards
        # Global leaderboard
        await redis_client.zincrby("leaderboard:global", points, user_id)
        
        # Platform-specific leaderboard
        if platform:
            await redis_client.zincrby(f"leaderboard:{platform}", points, user_id)
        
        # Update user's total points in database if session provided
        if session:
            # Update the user's total points
            result = await session.execute(
                "UPDATE users SET total_points = total_points + :points WHERE id = :user_id RETURNING username, total_points + :points as new_total",
                {"points": points, "user_id": user_id}
            )
            
            # Get the updated user information
            user_info = result.fetchone()
            if user_info:
                username = user_info[0]
                new_total = user_info[1]
                
                # Store user info for easy retrieval
                await redis_client.hset(f"user:{user_id}", mapping={
                    "username": username,
                    "total_points": new_total
                })
            
            await session.commit()
        
        logger.info(f"Added {points} points to user {user_id} for platform {platform}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding points: {e}")
        if session:
            await session.rollback()
        return False


async def top_n(platform: str = None, n: int = 100) -> list:
    """
    Get the top N users from the leaderboard
    
    Args:
        platform: Optional platform to filter by (twitter, instagram, etc.)
        n: Maximum number of users to return (default: 100)
        
    Returns:
        list: List of user dictionaries with id, username, and total_points
    """
    try:
        # Determine which leaderboard to use
        leaderboard_key = f"leaderboard:{platform}" if platform else "leaderboard:global"
        
        # Get top users from Redis sorted set
        top_users = await redis_client.zrevrange(leaderboard_key, 0, n-1, withscores=True)
        
        # Format the results
        leaderboard = []
        for user_id, score in top_users:
            # Get user details from Redis hash
            user_info = await redis_client.hgetall(f"user:{user_id}")
            
            leaderboard.append({
                "id": user_id,
                "username": user_info.get("username", "unknown"),
                "total_points": int(score)
            })
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting top users: {e}")
        return []