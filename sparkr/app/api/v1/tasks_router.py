from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from sparkr.app.models.schemas import TaskCreate, TaskResponse
from sparkr.app.models.models import Task, Campaign
from sparkr.app.db.session import get_session

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    """Create a new task"""
    # Verify campaign exists
    result = await session.execute(select(Campaign).where(Campaign.id == task.campaign_id))
    campaign = result.scalar_one_or_none()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {task.campaign_id} not found"
        )
    
    # Create new task from the request data
    db_task = Task(
        campaign_id=task.campaign_id,
        title=task.title,
        description=task.description,
        platform=task.platform,
        points=task.points,
        status="active"
    )
    
    # Add to database
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    
    return db_task


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(campaign_id: str = None, session: AsyncSession = Depends(get_session)):
    """Get all tasks, optionally filtered by campaign_id"""
    # Build query
    query = select(Task)
    
    # Filter by campaign_id if provided
    if campaign_id:
        query = query.where(Task.campaign_id == campaign_id)
    
    # Execute query
    result = await session.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """Get a specific task by ID"""
    # Query task by ID
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_data: TaskCreate, session: AsyncSession = Depends(get_session)):
    """Update a task"""
    # Query task by ID
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Verify campaign exists if campaign_id is being updated
    if task.campaign_id != task_data.campaign_id:
        campaign_result = await session.execute(select(Campaign).where(Campaign.id == task_data.campaign_id))
        campaign = campaign_result.scalar_one_or_none()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign with ID {task_data.campaign_id} not found"
            )
    
    # Update task fields
    task.campaign_id = task_data.campaign_id
    task.title = task_data.title
    task.description = task_data.description
    task.platform = task_data.platform
    task.points = task_data.points
    
    # Save to database
    await session.commit()
    await session.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, session: AsyncSession = Depends(get_session)):
    """Delete a task"""
    # Query task by ID
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Delete from database
    await session.delete(task)
    await session.commit()
    
    return None