# endpoints/scheduled_post.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from services.database.database import get_db
from services.models.scheduled_post_model import ScheduledPost, PostStatus

router = APIRouter(prefix="/post", tags=["Scheduled Post"])

class SchedulePostRequest(BaseModel):
    user_id: str
    platform: str
    post_payload: dict  # caption, image_url, etc.
    scheduled_time: datetime

@router.post("/schedule")
def schedule_post(data: SchedulePostRequest, db: Session = Depends(get_db)):
    post = ScheduledPost(
        user_id=data.user_id,
        platform=data.platform,
        post_payload=data.post_payload,
        scheduled_time=data.scheduled_time,
        status=PostStatus.pending
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"msg": "Post scheduled", "post_id": post.id}
