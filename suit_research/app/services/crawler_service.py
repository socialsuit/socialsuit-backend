"""
Crawler service for managing crawler data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.mongodb import MongoDBClient


class CrawlerService:
    """Service for crawler-related operations."""
    
    def __init__(self, mongodb: MongoDBClient):
        self.mongodb = mongodb
    
    async def save_crawler_data(self, data: Dict[str, Any]) -> str:
        """Save crawler data to MongoDB."""
        collection = self.mongodb.get_collection("crawler_data")
        
        # Add metadata
        data["_created_at"] = datetime.utcnow()
        data["_type"] = "crawler_result"
        
        result = await collection.insert_one(data)
        return str(result.inserted_id)
    
    async def get_crawler_data(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get crawler data from MongoDB."""
        collection = self.mongodb.get_collection("crawler_data")
        
        query = filters or {}
        cursor = collection.find(query).skip(skip).limit(limit).sort("_created_at", -1)
        
        results = []
        async for document in cursor:
            # Convert ObjectId to string
            document["_id"] = str(document["_id"])
            results.append(document)
        
        return results
    
    async def get_crawler_data_by_id(self, data_id: str) -> Optional[Dict[str, Any]]:
        """Get specific crawler data by ID."""
        from bson import ObjectId
        
        collection = self.mongodb.get_collection("crawler_data")
        
        try:
            document = await collection.find_one({"_id": ObjectId(data_id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except Exception:
            return None
    
    async def update_crawler_data(
        self, 
        data_id: str, 
        update_data: Dict[str, Any]
    ) -> bool:
        """Update crawler data."""
        from bson import ObjectId
        
        collection = self.mongodb.get_collection("crawler_data")
        
        try:
            update_data["_updated_at"] = datetime.utcnow()
            result = await collection.update_one(
                {"_id": ObjectId(data_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    async def delete_crawler_data(self, data_id: str) -> bool:
        """Delete crawler data."""
        from bson import ObjectId
        
        collection = self.mongodb.get_collection("crawler_data")
        
        try:
            result = await collection.delete_one({"_id": ObjectId(data_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    async def get_crawler_stats(self) -> Dict[str, Any]:
        """Get crawler statistics."""
        collection = self.mongodb.get_collection("crawler_data")
        
        total_count = await collection.count_documents({})
        
        # Get recent data count (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = await collection.count_documents({
            "_created_at": {"$gte": yesterday}
        })
        
        return {
            "total_documents": total_count,
            "recent_documents": recent_count,
            "last_updated": datetime.utcnow().isoformat()
        }