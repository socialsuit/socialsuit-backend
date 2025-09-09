from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum


class PlatformEnum(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"


class StatusEnum(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VerificationStatusEnum(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    AUTO_VERIFIED = "auto_verified"


# Campaign schemas
class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    end_date: date


class CampaignCreate(CampaignBase):
    pass


class CampaignResponse(CampaignBase):
    id: str
    status: StatusEnum
    created_at: datetime

    class Config:
        orm_mode = True


# Task schemas
class TaskBase(BaseModel):
    campaign_id: str
    title: str
    description: Optional[str] = None
    platform: PlatformEnum
    points: int = Field(ge=0)


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: str
    status: StatusEnum
    created_at: datetime

    class Config:
        orm_mode = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None


# Submission schemas
class SubmissionBase(BaseModel):
    task_id: str
    user_id: str
    submission_url: HttpUrl


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionResponse(SubmissionBase):
    id: str
    status: VerificationStatusEnum
    points_awarded: int = 0
    created_at: datetime

    class Config:
        orm_mode = True


# User schemas
class UserBase(BaseModel):
    email: str
    username: str


class UserCreate(UserBase):
    password: str


class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    is_active: bool = True

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    id: str
    total_points: int = 0
    created_at: datetime
    is_active: bool = True

    class Config:
        orm_mode = True


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None