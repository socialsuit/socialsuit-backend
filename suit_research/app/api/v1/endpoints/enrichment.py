"""Enrichment-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import get_db, AsyncSession
from app.tasks.enrichment_tasks import enrich_project_task, bulk_enrich_projects_task, scheduled_enrichment_task
from app.services.enrichment import EnrichmentService
from app.models.project import Project
from sqlalchemy import select

router = APIRouter()


class EnrichmentRequest(BaseModel):
    """Request model for project enrichment."""
    project_id: int
    config: Optional[Dict[str, Any]] = None


class BulkEnrichmentRequest(BaseModel):
    """Request model for bulk project enrichment."""
    project_ids: List[int]
    config: Optional[Dict[str, Any]] = None


class ScheduledEnrichmentRequest(BaseModel):
    """Request model for scheduled enrichment."""
    max_projects: Optional[int] = 50
    min_age_hours: Optional[int] = 24
    priority_projects: Optional[List[int]] = None


class EnrichmentResponse(BaseModel):
    """Response model for enrichment operations."""
    task_id: str
    status: str
    message: str
    project_id: Optional[int] = None
    project_ids: Optional[List[int]] = None


@router.post("/enrich", response_model=EnrichmentResponse)
async def enrich_project(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger manual enrichment for a specific project.
    
    Args:
        request: Enrichment request containing project_id and optional config
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Task information for the enrichment process
    """
    try:
        # Verify project exists
        result = await db.execute(
            select(Project).where(Project.id == request.project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=404, 
                detail=f"Project with ID {request.project_id} not found"
            )
        
        # Start enrichment task
        task = enrich_project_task.delay(request.project_id, request.config)
        
        return EnrichmentResponse(
            task_id=task.id,
            status="started",
            message=f"Enrichment started for project '{project.name}'",
            project_id=request.project_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting enrichment: {str(e)}")


@router.post("/enrich/bulk", response_model=EnrichmentResponse)
async def bulk_enrich_projects(
    request: BulkEnrichmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger bulk enrichment for multiple projects.
    
    Args:
        request: Bulk enrichment request containing project_ids and optional config
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Task information for the bulk enrichment process
    """
    try:
        if not request.project_ids:
            raise HTTPException(status_code=400, detail="No project IDs provided")
        
        if len(request.project_ids) > 100:
            raise HTTPException(
                status_code=400, 
                detail="Maximum 100 projects allowed per bulk enrichment request"
            )
        
        # Verify projects exist
        result = await db.execute(
            select(Project.id).where(Project.id.in_(request.project_ids))
        )
        existing_ids = [row[0] for row in result.fetchall()]
        
        missing_ids = set(request.project_ids) - set(existing_ids)
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Projects not found: {list(missing_ids)}"
            )
        
        # Start bulk enrichment task
        task = bulk_enrich_projects_task.delay(request.project_ids, request.config)
        
        return EnrichmentResponse(
            task_id=task.id,
            status="started",
            message=f"Bulk enrichment started for {len(request.project_ids)} projects",
            project_ids=request.project_ids
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting bulk enrichment: {str(e)}")


@router.post("/enrich/scheduled", response_model=EnrichmentResponse)
async def trigger_scheduled_enrichment(
    request: ScheduledEnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger scheduled enrichment for projects that need updates.
    
    Args:
        request: Scheduled enrichment configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Task information for the scheduled enrichment process
    """
    try:
        config = {
            'max_projects': request.max_projects,
            'min_age_hours': request.min_age_hours,
            'priority_projects': request.priority_projects or []
        }
        
        # Start scheduled enrichment task
        task = scheduled_enrichment_task.delay(config)
        
        return EnrichmentResponse(
            task_id=task.id,
            status="started",
            message=f"Scheduled enrichment started (max {request.max_projects} projects)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduled enrichment: {str(e)}")


@router.get("/status/{task_id}")
async def get_enrichment_status(task_id: str):
    """
    Get enrichment task status.
    
    Args:
        task_id: ID of the enrichment task
        
    Returns:
        Task status and results
    """
    try:
        from app.core.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.status,
            "result": None,
            "error": None
        }
        
        if task.ready():
            if task.successful():
                response["result"] = task.result
            else:
                response["error"] = str(task.info)
        else:
            # Task is still running, get current state info
            response["result"] = task.info
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@router.get("/project/{project_id}/enrichment")
async def get_project_enrichment_data(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current enrichment data for a project.
    
    Args:
        project_id: ID of the project
        db: Database session
        
    Returns:
        Current enrichment data and metadata
    """
    try:
        enrichment_service = EnrichmentService(db)
        
        # Get enrichment data
        enrichment_data = await enrichment_service.get_enrichment_data(project_id)
        
        # Get enrichment history
        enrichment_history = await enrichment_service.get_enrichment_history(project_id)
        
        # Get project basic info
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "enrichment_data": enrichment_data,
            "enrichment_history": enrichment_history,
            "last_enriched": project.meta_data.get('last_enriched') if project.meta_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting enrichment data: {str(e)}")