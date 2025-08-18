"""
Crawler-related endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.core.mongodb import get_mongodb, MongoDBClient
from app.tasks.crawler_tasks import start_crawler_task
from app.services.crawler_service import CrawlerService

router = APIRouter()


@router.post("/start")
async def start_crawler(
    crawler_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Start a new crawler task.
    """
    # Validate crawler config
    if not crawler_config.get("url"):
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Start crawler task in background
    task = start_crawler_task.delay(crawler_config)
    
    return {
        "task_id": task.id,
        "status": "started",
        "config": crawler_config
    }


@router.get("/status/{task_id}")
async def get_crawler_status(task_id: str):
    """
    Get crawler task status.
    """
    from app.core.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }


@router.get("/data")
async def get_crawler_data(
    skip: int = 0,
    limit: int = 100,
    mongodb: MongoDBClient = Depends(get_mongodb)
):
    """
    Get crawler data from MongoDB.
    """
    service = CrawlerService(mongodb)
    data = await service.get_crawler_data(skip=skip, limit=limit)
    return data