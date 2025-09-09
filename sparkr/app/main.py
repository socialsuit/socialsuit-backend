from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from sparkr.app.core.config import settings
from sparkr.app.core.logging import setup_logging
from sparkr.app.api.v1.auth_router import router as auth_router
from sparkr.app.api.v1.campaigns_router import router as campaigns_router
from sparkr.app.api.v1.tasks_router import router as tasks_router
from sparkr.app.api.v1.submissions_router import router as submissions_router
from sparkr.app.api.v1.leaderboard_router import router as leaderboard_router
from sparkr.app.api.v1.rewards_router import router as rewards_router
from sparkr.app.api.v1.admin_router import router as admin_router
from sparkr.app.middleware.admin import admin_middleware
from sparkr.app.middleware.request_logger import request_logging_middleware
from sparkr.app.middleware.rate_limiter import rate_limiting_middleware
from sparkr.app.middleware.sanitization_middleware import SanitizationMiddleware

# Setup logging and Sentry
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware in order (executed in reverse order)
app.middleware("http")(rate_limiting_middleware)  # First to execute
app.middleware("http")(request_logging_middleware)
app.middleware("http")(admin_middleware)  # Last to execute

# Add sanitization middleware
app.add_middleware(
    SanitizationMiddleware,
    exclude_paths=[f"{settings.API_V1_STR}/docs", f"{settings.API_V1_STR}/redoc", f"{settings.API_V1_STR}/openapi.json"]
)

# Import and add health routes
from app.api.health import add_health_routes
add_health_routes(app)

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(campaigns_router, prefix=settings.API_V1_STR)
from sparkr.app.api.v1.uploads_router import router as uploads_router
app.include_router(uploads_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(submissions_router, prefix=settings.API_V1_STR)
app.include_router(leaderboard_router, prefix=settings.API_V1_STR)
app.include_router(rewards_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/sparkr")


@app.get("/")
async def root():
    return {"message": "Welcome to Sparkr API"}


@app.get("/health")
async def health_check():
    """Health check endpoint
    
    Returns basic application health information and status.
    This endpoint is exempt from rate limiting.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "production" if not settings.DEBUG else "development"
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)