from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ConfigurationError
import os
from typing import Optional
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """
    Async MongoDB connection manager with error handling and connection pooling.
    """
    _client: Optional[AsyncIOMotorClient] = None  # type: ignore
    _db: Optional[AsyncIOMotorDatabase] = None  # type: ignore
    
    @classmethod
    async def initialize(cls):
        """Initialize the MongoDB connection pool"""
        MONGO_URI = os.getenv("MONGO_URI")
        if not MONGO_URI:
            raise ConfigurationError("MONGO_URI environment variable not set")

        try:
            cls._client = AsyncIOMotorClient(
                MONGO_URI,
                maxPoolSize=100,          # Default connection pool size
                minPoolSize=10,           # Minimum connections
                connectTimeoutMS=5000,    # 5-second connection timeout
                socketTimeoutMS=30000,     # 30-second operation timeout
                serverSelectionTimeoutMS=5000  # 5-second server selection timeout
            )
            # Test the connection
            await cls._client.admin.command('ping')
            cls._db = cls._client["social_suit"]
            logger.info("✅ Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"🚨 MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected MongoDB error: {e}")
            raise

    @classmethod
    @asynccontextmanager
    async def get_db(cls):
        """Async context manager for database access"""
        if not cls._db:
            await cls.initialize()
        
        try:
            yield cls._db
        except Exception as e:
            logger.error(f"🔴 Database operation failed: {e}")
            raise

    @classmethod
    async def close_connection(cls):
        """Cleanly close the connection"""
        if cls._client:
            cls._client.close()
            logger.info("🔌 MongoDB connection closed")

# FastAPI integration example
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_db():
    await MongoDBManager.initialize()

@app.on_event("shutdown")
async def shutdown_db():
    await MongoDBManager.close_connection()

@app.get("/users")
async def get_users():
    async with MongoDBManager.get_db() as db:
        return await db.users.find().to_list(100)