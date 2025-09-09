from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel, HttpUrl

from app.models.schemas import SubmissionCreate, SubmissionResponse, VerificationStatusEnum
from app.models.models import Submission, Task, User
from app.models.reward import Reward
from app.db.session import get_session
from app.core.security import get_current_user
from app.services.verification import verify_submission
from app.services.points import calculate_points, award_points
from app.workers.tasks_worker import verify_submission_task

router = APIRouter(prefix="/submissions", tags=["submissions"])


class TaskSubmission(BaseModel):
    task_id: str
    submission_url: HttpUrl
    tweet_id: Optional[str] = None
    ig_post_id: Optional[str] = None
    proof_url: Optional[HttpUrl] = None


@router.post("/tasks/{task_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_task(
    task_id: str,
    proof_data: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Submit a completed task with proof URL"""
    # Verify task exists
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    # Check if user already submitted this task
    result = await session.execute(
        select(Submission).where(
            Submission.task_id == task_id,
            Submission.user_id == current_user.id
        )
    )
    existing_submission = result.scalar_one_or_none()
    
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted this task"
        )
    
    # Extract proof_url from the request data
    proof_url = proof_data.get("proof_url")
    if not proof_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proof URL is required"
        )
    
    # Create new submission
    db_submission = Submission(
        task_id=task_id,
        user_id=current_user.id,
        submission_url=str(proof_url),  # Use proof_url as submission_url
        proof_url=str(proof_url),
        status=VerificationStatusEnum.PENDING,
        points_awarded=0
    )
    
    # Add to database
    session.add(db_submission)
    await session.commit()
    await session.refresh(db_submission)
    
    # Enqueue background job for verification and points awarding
    verify_submission_task.delay(db_submission.id)
    
    # Return the submission with pending status
    # The background task will update the status and points
    await session.refresh(db_submission)
    
    return db_submission


@router.get("/", response_model=List[SubmissionResponse])
async def get_submissions(
    task_id: Optional[str] = None,
    status: Optional[VerificationStatusEnum] = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get submissions with optional filtering
    
    For regular users: Returns only their own submissions
    For admins: Returns all submissions with optional status filtering
    """
    # Start with a base query
    query = select(Submission)
    
    # Check if user is admin (you may need to adjust this based on your auth system)
    # For this implementation, we'll assume there's an is_admin field in the User model
    # If there isn't, you'll need to implement your own admin check logic
    is_admin = getattr(current_user, "is_admin", False)
    
    # For non-admin users, only show their own submissions
    if not is_admin:
        query = query.where(Submission.user_id == current_user.id)
    
    # Apply filters if provided
    if task_id:
        query = query.where(Submission.task_id == task_id)
        
    if status:
        query = query.where(Submission.status == status)
    
    # Execute query
    result = await session.execute(query)
    submissions = result.scalars().all()
    
    return submissions


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific submission by ID"""
    # Query submission by ID and user_id for security
    result = await session.execute(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == current_user.id
        )
    )
    submission = result.scalar_one_or_none()
    
    # Raise 404 if not found
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with ID {submission_id} not found or does not belong to you"
        )
    
    return submission


class ReviewSubmission(BaseModel):
    status: VerificationStatusEnum


@router.put("/{submission_id}/review", response_model=SubmissionResponse)
async def review_submission(
    submission_id: str,
    review_data: ReviewSubmission,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Review a submission (admin only)
    
    Allows admins to approve or reject a submission and award points if approved
    """
    # Check if user is admin
    is_admin = getattr(current_user, "is_admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can review submissions"
        )
    
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
    
    # Get the associated task to calculate points
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
    submission.status = review_data.status
    
    # If approved, calculate and award points
    if review_data.status == VerificationStatusEnum.VERIFIED:
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
            logger.error(f"Failed to award points for submission {submission.id}")
    
    # Save changes
    await session.commit()
    await session.refresh(submission)
    
    return submission