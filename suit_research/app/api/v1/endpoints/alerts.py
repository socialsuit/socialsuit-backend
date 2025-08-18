"""Alert API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.models.project import Project
from app.api.schemas.alert import (
    AlertCreateRequest,
    AlertUpdateRequest,
    AlertResponse,
    AlertListResponse
)

router = APIRouter()


# Mock function to get current user - replace with actual auth
async def get_current_user() -> int:
    """Mock function to get current user ID. Replace with actual authentication."""
    return 1  # Mock user ID


@router.get("/", response_model=AlertListResponse)
async def get_user_alerts(
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    is_active: Optional[str] = Query(None, description="Filter by active status"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Get user's alerts with optional filtering.
    
    - **skip**: Number of alerts to skip (for pagination)
    - **limit**: Maximum number of alerts to return
    - **alert_type**: Optional filter by alert type
    - **is_active**: Optional filter by active status (active/inactive)
    - **project_id**: Optional filter by project ID
    """
    query = select(Alert).where(Alert.user_id == current_user_id)
    
    # Apply filters
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if is_active:
        query = query.where(Alert.is_active == is_active)
    if project_id:
        query = query.where(Alert.project_id == project_id)
    
    # Add pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Get total count for pagination
    count_query = select(Alert).where(Alert.user_id == current_user_id)
    if alert_type:
        count_query = count_query.where(Alert.alert_type == alert_type)
    if is_active:
        count_query = count_query.where(Alert.is_active == is_active)
    if project_id:
        count_query = count_query.where(Alert.project_id == project_id)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return AlertListResponse(
        alerts=[AlertResponse.model_validate(alert) for alert in alerts],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Get alert by ID.
    
    - **alert_id**: The ID of the alert to retrieve
    """
    query = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user_id)
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return AlertResponse.model_validate(alert)


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Create a new alert.
    
    - **project_id**: The ID of the project to monitor
    - **alert_type**: Type of alert (funding_received, listing, token_price_threshold, etc.)
    - **threshold**: Optional threshold conditions for triggering the alert
    - **is_active**: Whether the alert is active (default: active)
    """
    # Verify project exists
    project_query = select(Project).where(Project.id == alert_data.project_id)
    project_result = await db.execute(project_query)
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if alert already exists for this user/project/type combination
    existing_query = select(Alert).where(
        and_(
            Alert.user_id == current_user_id,
            Alert.project_id == alert_data.project_id,
            Alert.alert_type == alert_data.alert_type
        )
    )
    existing_result = await db.execute(existing_query)
    existing_alert = existing_result.scalar_one_or_none()
    
    if existing_alert:
        raise HTTPException(
            status_code=400, 
            detail="Alert already exists for this project and alert type"
        )
    
    # Create new alert
    alert = Alert(
        user_id=current_user_id,
        project_id=alert_data.project_id,
        alert_type=alert_data.alert_type.value,
        threshold=alert_data.threshold,
        is_active=alert_data.is_active.value
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_data: AlertUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Update an existing alert.
    
    - **alert_id**: The ID of the alert to update
    - **alert_type**: Optional new alert type
    - **threshold**: Optional new threshold conditions
    - **is_active**: Optional new active status
    """
    query = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user_id)
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Update fields if provided
    if alert_data.alert_type is not None:
        alert.alert_type = alert_data.alert_type.value
    if alert_data.threshold is not None:
        alert.threshold = alert_data.threshold
    if alert_data.is_active is not None:
        alert.is_active = alert_data.is_active.value
    
    await db.commit()
    await db.refresh(alert)
    
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    """
    Delete an alert.
    
    - **alert_id**: The ID of the alert to delete
    """
    query = select(Alert).where(
        and_(Alert.id == alert_id, Alert.user_id == current_user_id)
    )
    result = await db.execute(query)
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "Alert deleted successfully", "alert_id": alert_id}