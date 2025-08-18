"""
Main API router for v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import status, research, crawler, protected, enrichment, investors, alerts, watchlist, projects, funding_rounds, webhooks
from app.api.v1 import auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(status.router, prefix="/status", tags=["status"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(funding_rounds.router, prefix="/funding_rounds", tags=["funding_rounds"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
api_router.include_router(protected.router, prefix="/protected", tags=["protected"])
api_router.include_router(enrichment.router, prefix="/enrichment", tags=["enrichment"])
api_router.include_router(investors.router, prefix="/investors", tags=["investors"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# OAuth2 endpoints (separate prefix)
oauth_router = APIRouter()
oauth_router.include_router(auth.oauth_router, tags=["oauth2"])