import os
import logging
import json
import time
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisManager:
    """Manages Redis connections and provides utility methods for Redis operations"""
    _redis_instance = None
    _redis_url = None
    
    @classmethod
    async def initialize(cls, redis_url: Optional[str] = None):
        """Initialize the Redis connection"""
        if redis_url:
            cls._redis_url = redis_url
        else:
            # Default Redis URL if not provided
            cls._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            cls._redis_instance = Redis.from_url(cls._redis_url, decode_responses=True)
            # Test connection
            await cls._redis_instance.ping()
            logger.info(f"✅ Redis connection established: {cls._redis_url}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            cls._redis_instance = None
            raise
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncIterator[Redis]:
        """Get a Redis connection"""
        if cls._redis_instance is None:
            await cls.initialize()
        
        try:
            yield cls._redis_instance
        except Exception as e:
            logger.error(f"❌ Redis operation failed: {e}")
            raise

# Redis cache decorator
def redis_cache(ttl_seconds: int = 300, key_prefix: str = ""):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a cache key based on function name, args, and kwargs
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"  
            
            # Try to get cached result
            async with RedisManager.get_connection() as redis:
                cached_result = await redis.get(cache_key)
                
                if cached_result:
                    try:
                        return json.loads(cached_result)
                    except json.JSONDecodeError:
                        # If not JSON, return as is
                        return cached_result
            
            # If not cached, execute the function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            try:
                serialized_result = json.dumps(result)
                async with RedisManager.get_connection() as redis:
                    await redis.set(cache_key, serialized_result, ex=ttl_seconds)
                    
                    # Log slow operations
                    if execution_time > 0.5:  # >500ms
                        logger.info(f"⚠️ Slow operation cached: {func.__name__} took {execution_time:.2f}s")
            except (TypeError, json.JSONDecodeError) as e:
                logger.warning(f"⚠️ Could not cache result for {func.__name__}: {e}")
            
            return result
        
        return wrapper
    
    return decorator