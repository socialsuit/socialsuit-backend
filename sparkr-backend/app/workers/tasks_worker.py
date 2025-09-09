from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import asyncio
from app.core.config import settings
from app.services.verification import verify_submission
from app.services.points import calculate_points, award_points
from app.models.models import Submission, Task, User
from app.models.schemas import VerificationStatusEnum
from app.db.session import async_session_maker
from loguru import logger

# Create Celery instance
celery_app = Celery(
    "sparkr",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="verify_submission", bind=True, max_retries=3, default_retry_delay=60)
def verify_submission_task(self, submission_id: str):
    """Background task to verify a submission and award points
    
    Args:
        submission_id: The ID of the submission to verify
        
    Returns:
        dict: Result of the verification process
    """
    try:
        # Run the async verification process
        return asyncio.run(_verify_submission_async(submission_id))
    except Exception as e:
        logger.error(f"Error in verification task: {e}")
        # Retry with exponential backoff
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        logger.info(f"Retrying task in {retry_delay} seconds (attempt {self.request.retries + 1})")
        raise self.retry(exc=e, countdown=retry_delay)


async def _verify_submission_async(submission_id: str):
    """Async implementation of submission verification
    
    Args:
        submission_id: The ID of the submission to verify
        
    Returns:
        dict: Result of the verification process
    """
    async with async_session_maker() as session:
        try:
            # Get the submission
            result = await session.execute(
                select(Submission).where(Submission.id == submission_id)
            )
            submission = result.scalar_one_or_none()
            
            if not submission:
                logger.error(f"Submission {submission_id} not found")
                return {"success": False, "error": "Submission not found"}
            
            # Skip if submission is not pending
            if submission.status != VerificationStatusEnum.PENDING:
                logger.info(f"Submission {submission_id} is already {submission.status}, skipping verification")
                return {"success": True, "skipped": True, "status": submission.status}
            
            # Get the task
            result = await session.execute(
                select(Task).where(Task.id == submission.task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task:
                logger.error(f"Task {submission.task_id} not found for submission {submission_id}")
                return {"success": False, "error": "Task not found"}
            
            logger.info(f"Verifying submission {submission_id} for task {task.id} by user {submission.user_id}")
            
            # Verify the submission
            is_verified = await verify_submission(submission, task)
            
            if is_verified:
                # Calculate points
                points = calculate_points(task.platform, submission)
                
                # Award points to user
                success = await award_points(
                    user_id=submission.user_id,
                    submission_id=submission.id,
                    points=points,
                    session=session
                )
                
                if success:
                    # Update submission status to auto_verified
                    submission.status = VerificationStatusEnum.AUTO_VERIFIED
                    submission.points_awarded = points
                    session.add(submission)
                    await session.commit()
                    
                    logger.info(f"Submission {submission_id} auto-verified successfully, awarded {points} points")
                    return {"success": True, "verified": True, "points": points, "status": "auto_verified"}
                else:
                    logger.error(f"Failed to award points for submission {submission_id}")
                    return {"success": False, "error": "Failed to award points"}
            else:
                # Update submission status to rejected
                submission.status = VerificationStatusEnum.REJECTED
                session.add(submission)
                await session.commit()
                
                logger.info(f"Submission {submission_id} rejected by auto-verification")
                return {"success": True, "verified": False, "status": "rejected"}
                
        except Exception as e:
            logger.error(f"Error in verification task: {e}")
            # Rollback session in case of error
            await session.rollback()
            return {"success": False, "error": str(e)}


@celery_app.task(name="process_campaign_analytics")
def process_campaign_analytics(campaign_id: str):
    """Background task to process analytics for a campaign"""
    try:
        # In a real implementation, you would process analytics data for the campaign
        # This is a placeholder implementation
        logger.info(f"Processing analytics for campaign {campaign_id}")
        
        # For demo purposes, we'll just return success
        return {"success": True, "message": "Analytics processing completed"}
        
    except Exception as e:
        logger.error(f"Error in analytics task: {e}")
        return {"success": False, "error": str(e)}