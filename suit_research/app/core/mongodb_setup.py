"""
MongoDB setup and initialization script.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDBSetup:
    """MongoDB setup and index management."""
    
    def __init__(self):
        self.client = None
        self.database = None
    
    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.MONGODB_DB_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def create_collections_and_indexes(self):
        """Create collections and indexes for MongoDB."""
        try:
            # Create raw_crawls collection with indexes
            raw_crawls_collection = self.database.raw_crawls
            
            # Create indexes for raw_crawls
            raw_crawls_indexes = [
                IndexModel([("source", ASCENDING)], name="idx_source"),
                IndexModel([("scraped_at", DESCENDING)], name="idx_scraped_at"),
                IndexModel([("processed", ASCENDING)], name="idx_processed"),
                IndexModel([("content_type", ASCENDING)], name="idx_content_type"),
                IndexModel([("source", ASCENDING), ("scraped_at", DESCENDING)], name="idx_source_scraped_at"),
                IndexModel([("metadata.status_code", ASCENDING)], name="idx_metadata_status_code", sparse=True),
            ]
            
            await raw_crawls_collection.create_indexes(raw_crawls_indexes)
            logger.info("Created indexes for raw_crawls collection")
            
            # Create crawl_stats collection with indexes
            crawl_stats_collection = self.database.crawl_stats
            
            crawl_stats_indexes = [
                IndexModel([("date", DESCENDING)], name="idx_date"),
                IndexModel([("source", ASCENDING)], name="idx_source"),
                IndexModel([("date", DESCENDING), ("source", ASCENDING)], name="idx_date_source", unique=True),
            ]
            
            await crawl_stats_collection.create_indexes(crawl_stats_indexes)
            logger.info("Created indexes for crawl_stats collection")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB collections and indexes: {e}")
            return False
    
    async def setup_database(self):
        """Complete database setup."""
        if not await self.connect():
            return False
        
        if not await self.create_collections_and_indexes():
            return False
        
        logger.info("MongoDB setup completed successfully")
        return True
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


async def setup_mongodb():
    """Setup MongoDB collections and indexes."""
    setup = MongoDBSetup()
    try:
        success = await setup.setup_database()
        return success
    finally:
        await setup.close()


async def main():
    """Main function for running MongoDB setup."""
    print("Setting up MongoDB collections and indexes...")
    success = await setup_mongodb()
    
    if success:
        print("✅ MongoDB setup completed successfully!")
    else:
        print("❌ MongoDB setup failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())