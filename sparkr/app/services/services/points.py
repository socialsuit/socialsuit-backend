from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import redis.asyncio as redis
from sparkr.app.models.models import Submission
from sparkr.app.models.reward import Reward
from sparkr.app.models.schemas import PlatformEnum
from sparkr.app.core.config import settings

# Create Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def calculate_points(task_type: PlatformEnum, submission: Submission) -> int:
    """Calculate points to award based on task type and submission
    
    Args:
        task_type: The platform type of the task
        submission: The submission object
        
    Returns:
        int: The number of points to award
    """
    # Base points from the task
    base_points = submission.task.points if submission.task else 0
    
    # Platform-specific bonuses
    platform_bonus = 0
    
    # Apply platform-specific bonuses
    if task_type == PlatformEnum.TWITTER:
        # Twitter tasks get a 10% bonus
        platform_bonus = int(base_points * 0.1)
    elif task_type == PlatformEnum.INSTAGRAM:
        # Instagram tasks get a 15% bonus
        platform_bonus = int(base_points * 0.15)
    elif task_type == PlatformEnum.FACEBOOK:
        # Facebook tasks get a 5% bonus
        platform_bonus = int(base_points * 0.05)
    elif task_type == PlatformEnum.TIKTOK:
        # TikTok tasks get a 20% bonus
        platform_bonus = int(base_points * 0.2)
    
    # Calculate total points
    total_points = base_points + platform_bonus
    
    logger.info(f"Calculated {total_points} points for {task_type} submission {submission.id}")
    return total_points


async def award_points(user_id: str, submission_id: str, points: int, session: AsyncSession) -> bool:
    """Award points to a user and record the reward
    
    Args:
        user_id: The ID of the user to award points to
        submission_id: The ID of the submission that earned the points
        points: The number of points to award
        session: The database session
        
    Returns:
        bool: True if points were awarded successfully, False otherwise
    """
    try:
        # Create a new reward record
        reward = Reward(
            user_id=user_id,
            submission_id=submission_id,
            points=points
        )
        session.add(reward)
        
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
        else:
            # Fallback if we couldn't get the updated info
            user_result = await session.execute(
                "SELECT username, total_points FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )
            user_data = user_result.fetchone()
            username = user_data[0] if user_data else "unknown"
            new_total = user_data[1] if user_data else points
        
        # Update the submission's points_awarded
        await session.execute(
            "UPDATE submissions SET points_awarded = :points WHERE id = :submission_id",
            {"points": points, "submission_id": submission_id}
        )
        
        # Get the task and platform information
        submission_result = await session.execute(
            """SELECT t.platform 
               FROM submissions s 
               JOIN tasks t ON s.task_id = t.id 
               WHERE s.id = :submission_id""",
            {"submission_id": submission_id}
        )
        platform_data = submission_result.fetchone()
        platform = platform_data[0] if platform_data else None
        
        # Commit database changes
        await session.commit()
        
        # Update Redis leaderboard
        try:
            # Global leaderboard
            await redis_client.zincrby("leaderboard:global", points, user_id)
            
            # Platform-specific leaderboard if platform is available
            if platform:
                await redis_client.zincrby(f"leaderboard:{platform}", points, user_id)
                
            # Store user info for easy retrieval
            await redis_client.hset(f"user:{user_id}", mapping={
                "username": username,
                "total_points": new_total
            })
            
            logger.info(f"Updated Redis leaderboard for user {user_id} with {points} points")
        except Exception as redis_error:
            # Log Redis error but don't fail the transaction
            logger.error(f"Error updating Redis leaderboard: {redis_error}")
        
        logger.info(f"Awarded {points} points to user {user_id} for submission {submission_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error awarding points: {e}")
        await session.rollback()
        return False


async def get_user_points(user_id: str, session: AsyncSession) -> int:
    """Get the total points for a user
    
    Args:
        user_id: The ID of the user to get points for
        session: The database session
        
    Returns:
        int: The total points for the user
    """
    try:
        # Try to get points from Redis first (faster)
        try:
            user_info = await redis_client.hgetall(f"user:{user_id}")
            if user_info and "total_points" in user_info:
                return int(user_info["total_points"])
        except Exception as redis_error:
            logger.error(f"Error getting user points from Redis: {redis_error}")
        
        # Fall back to database if Redis fails or doesn't have the data
        result = await session.execute(
            "SELECT total_points FROM users WHERE id = :user_id",
            {"user_id": user_id}
        )
        points = result.scalar_one_or_none() or 0
        
        # Update Redis with the latest data
        try:
            # Get username for Redis hash
            user_result = await session.execute(
                "SELECT username FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )
            username = user_result.scalar_one_or_none() or "unknown"
            
            # Update Redis hash
            await redis_client.hset(f"user:{user_id}", mapping={
                "username": username,
                "total_points": points
            })
            
            # Update Redis sorted sets
            await redis_client.zadd("leaderboard:global", {user_id: points})
        except Exception as redis_error:
            # Log Redis error but don't fail the function
            logger.error(f"Error updating Redis with user points: {redis_error}")
        
        return points
        
    except Exception as e:
        logger.error(f"Error getting user points: {e}")
        return 0


async def get_leaderboard(campaign_id: str = None, platform: str = None, limit: int = 10, session: AsyncSession = None) -> list:
    """Get the leaderboard of users with the most points
    
    Args:
        campaign_id: Optional campaign ID to filter by
        platform: Optional platform to filter by (twitter, instagram, etc.)
        limit: Maximum number of users to return
        session: Database session for SQL queries
        
    Returns:
        list: List of user dictionaries with id, username, and total_points
    """
    try:
        # Use Redis for global and platform-specific leaderboards
        if not campaign_id and platform:
            # Platform-specific leaderboard from Redis
            leaderboard_key = f"leaderboard:{platform}"
            try:
                # Get top users from Redis sorted set
                top_users = await redis_client.zrevrange(leaderboard_key, 0, limit-1, withscores=True)
                
                # Format the results
                leaderboard = []
                for user_id, score in top_users:
                    # Get user details from Redis hash
                    user_info = await redis_client.hgetall(f"user:{user_id}")
                    if user_info:
                        leaderboard.append({
                            "id": user_id,
                            "username": user_info.get("username", "unknown"),
                            "total_points": int(score)
                        })
                    else:
                        # Fallback to database if Redis doesn't have user info
                        if session:
                            user_result = await session.execute(
                                "SELECT username FROM users WHERE id = :user_id",
                                {"user_id": user_id}
                            )
                            username = user_result.scalar_one_or_none() or "unknown"
                            leaderboard.append({
                                "id": user_id,
                                "username": username,
                                "total_points": int(score)
                            })
                
                return leaderboard
            except Exception as redis_error:
                logger.error(f"Error getting leaderboard from Redis: {redis_error}")
                # Fall back to database query if Redis fails
        
        if not campaign_id and not platform:
            # Global leaderboard from Redis
            try:
                top_users = await redis_client.zrevrange("leaderboard:global", 0, limit-1, withscores=True)
                
                # Format the results
                leaderboard = []
                for user_id, score in top_users:
                    # Get user details from Redis hash
                    user_info = await redis_client.hgetall(f"user:{user_id}")
                    if user_info:
                        leaderboard.append({
                            "id": user_id,
                            "username": user_info.get("username", "unknown"),
                            "total_points": int(score)
                        })
                    else:
                        # Fallback to database if Redis doesn't have user info
                        if session:
                            user_result = await session.execute(
                                "SELECT username FROM users WHERE id = :user_id",
                                {"user_id": user_id}
                            )
                            username = user_result.scalar_one_or_none() or "unknown"
                            leaderboard.append({
                                "id": user_id,
                                "username": username,
                                "total_points": int(score)
                            })
                
                return leaderboard
            except Exception as redis_error:
                logger.error(f"Error getting global leaderboard from Redis: {redis_error}")
                # Fall back to database query if Redis fails
                if session:
                    result = await session.execute(
                        """
                        SELECT id, username, total_points 
                        FROM users 
                        ORDER BY total_points DESC 
                        LIMIT :limit
                        """,
                        {"limit": limit}
                    )
                    
                    # Convert to list of dictionaries
                    leaderboard = []
                    for row in result.fetchall():
                        leaderboard.append({
                            "id": row[0],
                            "username": row[1],
                            "total_points": row[2]
                        })
                    
                    return leaderboard
        
        # Campaign-specific leaderboard (always use database)
        if campaign_id and session:
            result = await session.execute(
                """
                SELECT u.id, u.username, SUM(s.points_awarded) as total_points 
                FROM users u 
                JOIN submissions s ON u.id = s.user_id 
                JOIN tasks t ON s.task_id = t.id 
                WHERE t.campaign_id = :campaign_id AND s.status = 'verified' 
                GROUP BY u.id, u.username 
                ORDER BY total_points DESC 
                LIMIT :limit
                """,
                {"campaign_id": campaign_id, "limit": limit}
            )
            
            # Convert to list of dictionaries
            leaderboard = []
            for row in result.fetchall():
                leaderboard.append({
                    "id": row[0],
                    "username": row[1],
                    "total_points": row[2]
                })
            
            return leaderboard
        
        # Default empty response if no valid parameters
        return []
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []