"""
Status and health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.database import get_db
from app.core.redis_client import get_redis, RedisClient
from app.core.mongodb import get_mongodb, MongoDBClient

router = APIRouter()


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Health check endpoint that verifies all services are running.
    """
    health_status = {
        "status": "ok",
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "mongodb": "unknown"
        }
    }
    
    # Check PostgreSQL
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        await redis.set("health_check", "ok", expire=10)
        health_status["services"]["redis"] = "healthy"
    except Exception:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check MongoDB
    try:
        await mongodb.database.command("ping")
        health_status["services"]["mongodb"] = "healthy"
    except Exception:
        health_status["services"]["mongodb"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    """
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    """
    return {"status": "alive"}