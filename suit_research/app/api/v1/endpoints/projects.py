"""Project-related API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, Dict
import math

from app.core.database import get_db
from app.core.auth_middleware import get_current_user
from app.models.project import Project
from app.models.user import User
from app.crud.project import project as project_crud
from app.api.schemas.project import (
    ProjectResponse,
    ProjectListResponse,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectCategory
)

router = APIRouter()


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for project name or description"),
    token_symbol: Optional[str] = Query(None, description="Filter by token symbol"),
    category: Optional[ProjectCategory] = Query(None, description="Filter by project category"),
    min_score: Optional[float] = Query(None, description="Minimum project score"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of projects with pagination and filtering.
    
    - **page**: Page number (starts from 1)
    - **per_page**: Number of items per page (max 100)
    - **search**: Search in project name and description
    - **token_symbol**: Filter by token symbol
    - **category**: Filter by project category (defi, layer_1, layer_2, nft, gaming, infrastructure, ai, dex, wallet, tooling)
    - **min_score**: Filter by minimum score
    """
    # Use CRUD method for filtering
    projects, total = await project_crud.get_projects_with_filters(
        db=db,
        skip=(page - 1) * per_page,
        limit=per_page,
        search=search,
        token_symbol=token_symbol,
        category=category.value if category else None,
        min_score=min_score
    )
    
    # Calculate pagination info
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    has_next = page < total_pages
    has_prev = page > 1
    
    return ProjectListResponse(
        items=[ProjectResponse.model_validate(project) for project in projects],
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
        has_prev=has_prev
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific project by ID.
    
    - **project_id**: The ID of the project to retrieve
    """
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.model_validate(project)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project with automatic category detection.
    
    Requires authentication. If no category is provided, it will be automatically detected
    based on the project's name, description, website, and token symbol.
    """
    # Use CRUD method which includes category detection
    project = await project_crud.create_with_category_detection(db=db, obj_in=project_data)
    
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing project with automatic category detection.
    
    Requires authentication. If category is not provided in the update data,
    it will be automatically detected if the project doesn't already have one.
    """
    # Get existing project
    project = await project_crud.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Use CRUD method which includes category detection
    updated_project = await project_crud.update_with_category_detection(
        db=db, db_obj=project, obj_in=project_data
    )
    
    return ProjectResponse.model_validate(updated_project)


@router.get("/categories/stats", response_model=Dict[str, int])
async def get_category_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get project count statistics by category.
    
    Returns a dictionary with category names as keys and project counts as values.
    """
    stats = await project_crud.get_category_statistics(db=db)
    return stats


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project.
    
    Requires authentication.
    """
    # Get existing project
    project = await project_crud.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete project using CRUD method
    await project_crud.remove(db=db, id=project_id)