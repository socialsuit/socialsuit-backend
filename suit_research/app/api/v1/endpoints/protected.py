"""
Protected endpoints demonstrating authentication and authorization.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from app.core.auth_middleware import (
    require_scope,
    require_auth,
    AuthContext
)


router = APIRouter()


@router.get(
    "/public",
    summary="Public Data",
    description="Get public project data (requires read:public scope)"
)
async def get_public_data(
    auth_context: AuthContext = Depends(require_scope("read:public"))
):
    """Get public project data."""
    return {
        "message": "This is public project data",
        "data": [
            {"id": 1, "name": "Bitcoin", "symbol": "BTC"},
            {"id": 2, "name": "Ethereum", "symbol": "ETH"},
            {"id": 3, "name": "Solana", "symbol": "SOL"}
        ],
        "auth_info": {
            "auth_type": auth_context.auth_type,
            "scopes": auth_context.scopes
        }
    }


@router.get(
    "/funding",
    summary="Funding Data",
    description="Get funding round data (requires read:funding scope)"
)
async def get_funding_data(
    auth_context: AuthContext = Depends(require_scope("read:funding"))
):
    """Get funding round data."""
    return {
        "message": "This is funding round data",
        "data": [
            {
                "id": 1,
                "project": "Solana",
                "round": "Series A",
                "amount": 20000000,
                "date": "2021-06-09"
            },
            {
                "id": 2,
                "project": "Polygon",
                "round": "Seed",
                "amount": 450000,
                "date": "2019-04-03"
            }
        ],
        "auth_info": {
            "auth_type": auth_context.auth_type,
            "scopes": auth_context.scopes
        }
    }


@router.get(
    "/investors",
    summary="Investor Data",
    description="Get investor data (requires read:investors scope)"
)
async def get_investor_data(
    auth_context: AuthContext = Depends(require_scope("read:investors"))
):
    """Get investor data."""
    return {
        "message": "This is investor data",
        "data": [
            {
                "id": 1,
                "name": "Andreessen Horowitz",
                "type": "VC",
                "portfolio_count": 150
            },
            {
                "id": 2,
                "name": "Coinbase Ventures",
                "type": "Corporate VC",
                "portfolio_count": 200
            }
        ],
        "auth_info": {
            "auth_type": auth_context.auth_type,
            "scopes": auth_context.scopes
        }
    }


@router.post(
    "/webhooks",
    summary="Create Webhook",
    description="Create a webhook (requires write:webhooks scope)"
)
async def create_webhook(
    webhook_data: Dict[str, Any],
    auth_context: AuthContext = Depends(require_scope("write:webhooks"))
):
    """Create a webhook."""
    return {
        "message": "Webhook created successfully",
        "webhook": {
            "id": 123,
            "url": webhook_data.get("url", "https://example.com/webhook"),
            "events": webhook_data.get("events", ["funding.created"]),
            "created_at": "2024-01-15T10:30:00Z"
        },
        "auth_info": {
            "auth_type": auth_context.auth_type,
            "scopes": auth_context.scopes
        }
    }


@router.get(
    "/admin/stats",
    summary="Admin Statistics",
    description="Get admin statistics (requires admin scope)"
)
async def get_admin_stats(
    auth_context: AuthContext = Depends(require_scope("admin"))
):
    """Get admin statistics."""
    return {
        "message": "This is admin-only data",
        "stats": {
            "total_projects": 1250,
            "total_funding_rounds": 3400,
            "total_investors": 890,
            "api_requests_today": 15420
        },
        "auth_info": {
            "auth_type": auth_context.auth_type,
            "scopes": auth_context.scopes
        }
    }