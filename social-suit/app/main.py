from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
import os

# Import exception handlers from shared package
from shared.middleware.exception_handlers import register_exception_handlers

# Import security components
from social_suit.app.services.security.rate_limiter import RateLimiter, RateLimitConfig
from social_suit.app.services.security.security_middleware import SecurityMiddleware
from social_suit.app.services.security.security_config import (
    security_settings,
    RATE_LIMIT_CONFIG,
    get_security_middleware_config
)

# Auth routers
from social_suit.app.services.auth.platform.connect_router import router as connect_router
from social_suit.app.services.auth.wallet.auth_router import router as wallet_auth_router
from social_suit.app.services.auth.email.auth_router import router as email_auth_router
from social_suit.app.services.auth.protected_routes import router as protected_router

# Endpoint routers - using secure versions where available
from social_suit.app.services.endpoint.recycle import router as recycle_router
from social_suit.app.services.endpoint.analytics import router as analytics_router
from social_suit.app.services.endpoint.secure_analytics_api import router as analytics_api_router
from social_suit.app.services.endpoint.secure_scheduled_post_api import router as scheduled_post_router
from social_suit.app.services.endpoint.schedule import router as schedule_router
from social_suit.app.services.endpoint.thumbnail import router as thumbnail_router
from social_suit.app.services.endpoint.content import router as content_router
from social_suit.app.services.endpoint.ab_test import router as ab_test_router
from social_suit.app.services.endpoint.engage import router as engage_router
from social_suit.app.services.endpoint.customize import router as customize_router
from social_suit.app.services.endpoint import connect, callback, schedule

# Database setup
from social_suit.app.services.database.database import Base, engine
from social_suit.app.services.database.postgresql import init_db_pool, get_db_connection
from social_suit.app.services.database.mongodb import MongoDBManager
from social_suit.app.services.database.redis import RedisManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FastApiIntegration(),
            AsyncioIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("ENVIRONMENT", "development"),
    )
    logger.info("Sentry initialized for Social Suit")
else:
    logger.warning("Sentry DSN not found, error tracking disabled")

# Create FastAPI app
app = FastAPI(
    title="Social Suit API",
    description="A comprehensive social media management platform with enhanced security",
    version="2.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

# Import and setup middleware
from app.middleware import setup_middleware

# Import metrics setup
from app.services.monitoring.metrics import setup_metrics

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
        },
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "/api/v1/auth/authorize",
                    "tokenUrl": "/api/v1/auth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access"
                    }
                }
            }
        }
    }
    
    # Apply security globally
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
setup_middleware(app)

# -------------------------------
# 🔌 Connect to External Services
# -------------------------------
@app.on_event("startup")
async def connect_services():
    # Initialize security components first
    await initialize_security()
    
    # ✅ PostgreSQL
    await init_db_pool()
    print("✅ PostgreSQL Connected")

    # ✅ MongoDB
    await MongoDBManager.initialize()
    print("✅ MongoDB Connected")

    # ✅ Redis
    await RedisManager.initialize()
    async with RedisManager.get_connection() as redis:
        is_redis_connected = await redis.ping()
        print("✅ Redis Connected:", is_redis_connected)

# Initialize security components
async def initialize_security():
    """Initialize security components."""
    try:
        # Initialize Redis for rate limiting
        await RedisManager.initialize()
        logger.info("Redis initialized for security features")
        
        # Create rate limiter
        rate_limit_config = RateLimitConfig(**RATE_LIMIT_CONFIG)
        rate_limiter = RateLimiter(rate_limit_config)
        
        # Add comprehensive security middleware
        app.add_middleware(
            SecurityMiddleware,
            rate_limiter=rate_limiter,
            enable_rate_limiting=True,
            enable_security_headers=True,
            enable_input_validation=True,
            enable_ip_filtering=True,
            enable_audit_logging=True
        )
        
        logger.info("Security middleware initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize security components: {e}")
        # Continue without security features in development
        logger.warning("Running without enhanced security features")

# -------------------------------
# ❌ Disconnect All Services
# -------------------------------
@app.on_event("shutdown")
async def shutdown_services():
    from services.database.postgresql import close_db_pool
    await close_db_pool()
    print("🔌 PostgreSQL Connection Closed")

    await MongoDBManager.close_connection()
    print("🔌 MongoDB Connection Closed")

    await RedisManager.close()
    print("🔌 Redis Connection Closed")

# -------------------------------
# Database Table Initialization
# -------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------
# Enable CORS for Frontend
# -------------------------------
# Add CORS middleware (after security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_settings.cors_allow_origins,
    allow_credentials=security_settings.cors_allow_credentials,
    allow_methods=security_settings.cors_allow_methods,
    allow_headers=security_settings.cors_allow_headers,
)

# Register exception handlers for standardized error responses
register_exception_handlers(app)

# Setup Prometheus metrics
setup_metrics(app)

# Include routers-------------------------------
# Include Routers
# -------------------------------
# API v1 Endpoint Routers
app.include_router(content_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(scheduled_post_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(analytics_api_router, prefix="/api/v1")
app.include_router(recycle_router, prefix="/api/v1")
app.include_router(ab_test_router, prefix="/api/v1")
app.include_router(thumbnail_router, prefix="/api/v1")
app.include_router(engage_router, prefix="/api/v1")
app.include_router(customize_router, prefix="/api/v1")
app.include_router(connect.router, prefix="/api/v1")
app.include_router(callback.router, prefix="/api/v1")

# Auth routes
app.include_router(wallet_auth_router)
app.include_router(email_auth_router)
app.include_router(protected_router, prefix="/auth")
app.include_router(connect_router)

# -------------------------------
# Root Endpoint
# -------------------------------
@app.get("/")
def home():
    return {"msg": "🚀 Social Suit Backend Running"}



