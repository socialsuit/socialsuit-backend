from fastapi import Depends
from typing import AsyncGenerator, Any

from social_suit.app.services.database.mongodb import MongoDBManager
from social_suit.app.services.database.redis import RedisManager
from social_suit.app.services.database.postgresql import get_db_connection
from social_suit.app.services.database.database import get_db  # Import get_db from database.py

async def get_mongodb() -> AsyncGenerator[Any, None]:
    """
    Dependency provider for MongoDB connection
    """
    async with MongoDBManager.get_db() as db:
        yield db

async def get_redis() -> AsyncGenerator[Any, None]:
    """
    Dependency provider for Redis connection
    """
    async with RedisManager.get_connection() as redis:
        yield redis

async def get_postgres_connection() -> AsyncGenerator[Any, None]:
    """
    Dependency provider for raw PostgreSQL connection
    """
    async with get_db_connection() as conn:
        yield conn