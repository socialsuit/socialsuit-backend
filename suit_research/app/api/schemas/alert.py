"""Pydantic schemas for alert and watchlist API responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum


class AlertType(str, Enum):
    """Alert types enum."""
    FUNDING_RECEIVED = "funding_received"
    LISTING = "listing"
    TOKEN_PRICE_THRESHOLD = "token_price_threshold"
    SCORE_CHANGE = "score_change"
    NEWS = "news"


class AlertStatus(str, Enum):
    """Alert status enum."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class AlertCreateRequest(BaseModel):
    """Request schema for creating an alert."""
    project_id: int
    alert_type: AlertType
    threshold: Optional[Dict[str, Any]] = None
    is_active: AlertStatus = AlertStatus.ACTIVE


class AlertUpdateRequest(BaseModel):
    """Request schema for updating an alert."""
    alert_type: Optional[AlertType] = None
    threshold: Optional[Dict[str, Any]] = None
    is_active: Optional[AlertStatus] = None


class AlertResponse(BaseModel):
    """Response schema for alert information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    project_id: int
    alert_type: str
    threshold: Optional[Dict[str, Any]] = None
    is_active: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None


class AlertListResponse(BaseModel):
    """Response schema for alert list with pagination."""
    alerts: List[AlertResponse]
    total: int
    skip: int
    limit: int


class WatchlistCreateRequest(BaseModel):
    """Request schema for creating a watchlist entry."""
    project_id: int
    notes: Optional[str] = None


class WatchlistUpdateRequest(BaseModel):
    """Request schema for updating a watchlist entry."""
    notes: Optional[str] = None


class WatchlistResponse(BaseModel):
    """Response schema for watchlist information."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    project_id: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class WatchlistListResponse(BaseModel):
    """Response schema for watchlist with pagination."""
    watchlist: List[WatchlistResponse]
    total: int
    skip: int
    limit: int


class NotificationResponse(BaseModel):
    """Response schema for notification information."""
    id: int
    user_id: int
    alert_id: int
    project_id: int
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None