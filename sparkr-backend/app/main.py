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

# Import exception handlers from shared package
from shared.middleware.exception_handlers import register_exception_handlers

# Setup logging and Sentry
setup_logging()

# Import metrics setup
from app.core.metrics import setup_metrics

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Define security scheme for OpenAPI documentation
from fastapi.openapi.models import SecurityScheme
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token"
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and setup shared middleware
from app.middleware import setup_middleware
setup_middleware(app)

# Add application-specific middleware
app.middleware("http")(admin_middleware)

# Register exception handlers for standardized error responses
register_exception_handlers(app)

# Setup Prometheus metrics
setup_metrics(app)

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