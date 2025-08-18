"""
Redis client configuration and utilities.
"""

import redis.asyncio as redis
from typing import Optional, Any
import json
import pickle
from datetime import timedelta

from app.core.config import settings


class RedisClient:
    """Redis client wrapper with utility methods."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def init_redis(self) -> None:
        """Initialize Redis connection."""
        self.redis = redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_DB,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self.redis:
            return None
        return await self.redis.get(key)
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """Set key-value pair with optional expiration."""
        if not self.redis:
            return False
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.redis.set(key, value, ex=expire)
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        if not self.redis:
            return False
        return bool(await self.redis.delete(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            return False
        return bool(await self.redis.exists(key))
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment key value."""
        if not self.redis:
            return 0
        return await self.redis.incr(key, amount)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key."""
        if not self.redis:
            return False
        return await self.redis.expire(key, seconds)
    
    async def get_json(self, key: str) -> Optional[dict]:
        """Get JSON value by key."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: dict, 
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value with optional expiration."""
        return await self.set(key, json.dumps(value), expire)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client."""
    return redis_client


async def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    return redis_client


async def init_redis() -> None:
    """Initialize Redis connection."""
    await redis_client.init_redis()


# Rate limiting utilities
async def check_rate_limit(
    key: str, 
    limit: int = None, 
    window: int = 60
) -> tuple[bool, int]:
    """
    Check rate limit for a key.
    
    Args:
        key: Rate limit key (e.g., user_id, ip_address)
        limit: Maximum requests per window (default from settings)
        window: Time window in seconds
    
    Returns:
        Tuple of (is_allowed, current_count)
    """
    if limit is None:
        limit = settings.RATE_LIMIT_PER_MINUTE
    
    current = await redis_client.incr(key)
    
    if current == 1:
        await redis_client.expire(key, window)
    
    return current <= limit, current