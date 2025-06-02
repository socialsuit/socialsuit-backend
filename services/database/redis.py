import aioredis
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
import logging

# لوگنگ سیٹ اپ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisManager:
    _pool: Optional[aioredis.Redis] = None

    @classmethod
    async def initialize(cls):
        """Redis کنکشن پول کو شروع کرتا ہے"""
        try:
            cls._pool = await aioredis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True,
                max_connections=20,  # زیادہ کارکردگی کے لیے کنکشنز کی زیادہ سے زیادہ تعداد
                socket_timeout=5,    # 5 سیکنڈ میں ٹائم آؤٹ
                socket_keepalive=True
            )
            logger.info("✅ Redis connection pool initialized")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncIterator[aioredis.Redis]:
        """کنکشن کو خودکار طریقے سے کلوز کرنے کے لیے کنٹیکسٹ مینیجر"""
        if not cls._pool:
            await cls.initialize()
        
        try:
            yield cls._pool
        except aioredis.RedisError as e:
            logger.error(f"🔴 Redis operation failed: {e}")
            raise

    @classmethod
    async def close(cls):
        """کنکشن پول کو صحیح طریقے سے بند کرتا ہے"""
        if cls._pool:
            await cls._pool.close()
            logger.info("🔌 Redis connection pool closed")

# مثال: Nonce مینجمنٹ
async def set_nonce(user_id: str, nonce: str, ttl: int = 300) -> bool:
    async with RedisManager.get_connection() as redis:
        try:
            return await redis.set(f"nonce:{user_id}", nonce, ex=ttl)
        except aioredis.RedisError:
            return False

async def verify_nonce(user_id: str, nonce: str) -> bool:
    async with RedisManager.get_connection() as redis:
        stored_nonce = await redis.get(f"nonce:{user_id}")
        return stored_nonce == nonce

# FastAPI انٹیگریشن مثال
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
    nonce = os.urandom(16).hex()  # محفوظ رینڈم nonce
    success = await set_nonce(user_id, nonce)
    if not success:
        raise HTTPException(500, "Failed to set nonce")
    return {"nonce": nonce}

@app.post("/verify-nonce/{user_id}")
async def verify_nonce_endpoint(user_id: str, nonce: str):
    is_valid = await verify_nonce(user_id, nonce)
    return {"valid": is_valid}