"""
MongoDB configuration and client management.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client wrapper."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def init_mongodb(self) -> None:
        """Initialize MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
    
    def get_collection(self, collection_name: str):
        """Get collection by name."""
        if not self.database:
            raise RuntimeError("MongoDB not initialized")
        return self.database[collection_name]
    
    async def health_check(self) -> bool:
        """Check MongoDB health."""
        try:
            if not self.client:
                return False
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False


# Global MongoDB client instance
mongodb_client = MongoDBClient()


async def get_mongodb() -> MongoDBClient:
    """Dependency to get MongoDB client."""
    return mongodb_client


async def init_mongodb() -> None:
    """Initialize MongoDB connection."""
    await mongodb_client.init_mongodb()


# Collection helpers
async def get_crawler_data_collection():
    """Get crawler data collection."""
    return mongodb_client.get_collection("crawler_data")


async def get_raw_research_collection():
    """Get raw research data collection."""
    return mongodb_client.get_collection("raw_research")


async def get_logs_collection():
    """Get logs collection."""
    return mongodb_client.get_collection("logs")