from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.models.schemas import SubmissionResponse, VerificationStatusEnum
from app.models.models import Submission, Task, User, Campaign
from app.db.session import get_session
from app.services.points import calculate_points, award_points

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/submissions", response_model=List[SubmissionResponse])
async def get_admin_submissions(
    status: Optional[VerificationStatusEnum] = Query(None, description="Filter by submission status"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_session),
):
    """
    Admin endpoint to list submissions with optional filtering
    """
    query = select(Submission)
    
    # Apply filters if provided
    if status:
        query = query.where(Submission.status == status)
    if task_id:
        query = query.where(Submission.task_id == task_id)
    if campaign_id:
        # Join with Task to filter by campaign_id
        query = query.join(Task).where(Task.campaign_id == campaign_id)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    submissions = result.scalars().all()
    
    return submissions


@router.put("/submissions/{submission_id}/approve", response_model=SubmissionResponse)
async def approve_submission(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Admin endpoint to approve a submission
    """
    # Get the submission
    result = await session.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with ID {submission_id} not found"
        )
    
    # Get the associated task
    result = await session.execute(
        select(Task).where(Task.id == submission.task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task associated with this submission not found"
        )
    
    # Update submission status
    submission.status = VerificationStatusEnum.VERIFIED
    
    # Calculate points based on task
    points = calculate_points(task.platform, submission)
    
    # Award points to the user
    success = await award_points(
        user_id=submission.user_id,
        submission_id=submission.id,
        points=points,
        session=session
    )
    
    if success:
        submission.points_awarded = points
    else:
        # If points couldn't be awarded, still approve but log the issue
        print(f"Failed to award points for submission {submission.id}")
    
    # Save changes
    await session.commit()
    await session.refresh(submission)
    
    return submission


@router.put("/submissions/{submission_id}/reject", response_model=SubmissionResponse)
async def reject_submission(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Admin endpoint to reject a submission
    """
    # Get the submission
    result = await session.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with ID {submission_id} not found"
        )
    
    # Update submission status
    submission.status = VerificationStatusEnum.REJECTED
    
    # Save changes
    await session.commit()
    await session.refresh(submission)
    
    return submission


@router.get("/campaigns/stats")
async def get_campaign_stats(
    campaign_id: Optional[str] = Query(None, description="Filter by campaign ID"),
    session: AsyncSession = Depends(get_session),
):
    """
    Admin endpoint to get campaign statistics
    """
    # Base query for campaigns
    campaign_query = select(Campaign)
    if campaign_id:
        campaign_query = campaign_query.where(Campaign.id == campaign_id)
    
    # Execute campaign query
    result = await session.execute(campaign_query)
    campaigns = result.scalars().all()
    
    # Collect stats for each campaign
    stats = []
    for campaign in campaigns:
        # Get task count
        task_count_query = select(func.count(Task.id)).where(Task.campaign_id == campaign.id)
        result = await session.execute(task_count_query)
        task_count = result.scalar_one()
        
        # Get submission counts by status
        submission_stats = {}
        for status in VerificationStatusEnum:
            count_query = select(func.count(Submission.id)).\
                join(Task, Submission.task_id == Task.id).\
                where(Task.campaign_id == campaign.id, Submission.status == status)
            result = await session.execute(count_query)
            submission_stats[status.value] = result.scalar_one()
        
        # Get total points awarded
        points_query = select(func.sum(Submission.points_awarded)).\
            join(Task, Submission.task_id == Task.id).\
            where(Task.campaign_id == campaign.id)
        result = await session.execute(points_query)
        total_points = result.scalar_one() or 0
        
        # Get unique participants count
        participants_query = select(func.count(func.distinct(Submission.user_id))).\
            join(Task, Submission.task_id == Task.id).\
            where(Task.campaign_id == campaign.id)
        result = await session.execute(participants_query)
        participant_count = result.scalar_one()
        
        # Compile stats
        campaign_stats = {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "task_count": task_count,
            "submission_stats": submission_stats,
            "total_points_awarded": total_points,
            "participant_count": participant_count
        }
        
        stats.append(campaign_stats)
    
    return stats