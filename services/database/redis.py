import os
import logging
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisManager:
    _pool: Optional[Redis] = None

    @classmethod
    async def initialize(cls):
        """Initialize Redis connection pool"""
        try:
            cls._pool = Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True,
                max_connections=20,
                socket_timeout=5,
                socket_keepalive=True
            )
            logger.info("✅ Redis connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncIterator[Redis]:
        """Context manager for redis connection"""
        if not cls._pool:
            await cls.initialize()
        
        try:
            yield cls._pool
        except Exception as e:
            logger.error(f"🔴 Redis operation failed: {e}")
            raise

    @classmethod
    async def close(cls):
        """Properly close the Redis connection pool"""
        if cls._pool:
            await cls._pool.close()
            logger.info("🔌 Redis connection pool closed")

# Nonce Functions
async def set_nonce(user_id: str, nonce: str, ttl: int = 300) -> bool:
    async with RedisManager.get_connection() as redis:
        try:
            result = await redis.set(f"nonce:{user_id}", nonce, ex=ttl)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to set nonce: {e}")
            return False

async def verify_nonce(user_id: str, nonce: str) -> bool:
    async with RedisManager.get_connection() as redis:
        try:
            stored_nonce = await redis.get(f"nonce:{user_id}")
            return stored_nonce == nonce
        except Exception as e:
            logger.error(f"❌ Failed to verify nonce: {e}")
            return False

# FastAPI Integration Example
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.on_event("startup")
async def startup():
    await RedisManager.initialize()

@app.on_event("shutdown")
async def shutdown():
    await RedisManager.close()

@app.post("/generate-nonce/{user_id}")
async def generate_nonce(user_id: str):
    nonce = os.urandom(16).hex()
    success = await set_nonce(user_id, nonce)
    if not success:
        raise HTTPException(500, "Failed to set nonce")
    return {"nonce": nonce}

@app.post("/verify-nonce/{user_id}")
async def verify_nonce_endpoint(user_id: str, nonce: str):
    is_valid = await verify_nonce(user_id, nonce)
    return {"valid": is_valid}
