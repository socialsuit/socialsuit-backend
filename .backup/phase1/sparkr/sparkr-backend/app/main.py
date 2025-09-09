from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.auth_router import router as auth_router
from app.api.v1.campaigns_router import router as campaigns_router
from app.api.v1.tasks_router import router as tasks_router
from app.api.v1.submissions_router import router as submissions_router
from app.api.v1.leaderboard_router import router as leaderboard_router
from app.api.v1.rewards_router import router as rewards_router
from app.api.v1.admin_router import router as admin_router
from app.middleware.admin import admin_middleware
from app.middleware.request_logger import request_logging_middleware
from app.middleware.rate_limiter import rate_limiting_middleware

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

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(campaigns_router, prefix=settings.API_V1_STR)
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