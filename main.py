from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

# Import security components
from services.security.rate_limiter import RateLimiter, RateLimitConfig
from services.security.security_middleware import SecurityMiddleware
from services.security.security_config import (
    security_settings,
    RATE_LIMIT_CONFIG,
    get_security_middleware_config
)

# Auth routers
from services.auth.platform.connect_router import router as connect_router
from services.auth.wallet.auth_router import router as wallet_auth_router
from services.auth.email.auth_router import router as email_auth_router
from services.auth.protected_routes import router as protected_router

# Endpoint routers - using secure versions where available
from services.endpoint.recycle import router as recycle_router
from services.endpoint.analytics import router as analytics_router
from services.endpoint.secure_analytics_api import router as analytics_api_router
from services.endpoint.secure_scheduled_post_api import router as scheduled_post_router
from services.endpoint.schedule import router as schedule_router
from services.endpoint.thumbnail import router as thumbnail_router
from services.endpoint.content import router as content_router
from services.endpoint.ab_test import router as ab_test_router
from services.endpoint.engage import router as engage_router
from services.endpoint.customize import router as customize_router
from services.endpoint import connect, callback, schedule

# Database setup
from services.database.database import Base, engine
from services.database.postgresql import init_db_pool, get_db_connection
from services.database.mongodb import MongoDBManager
from services.database.redis import RedisManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Social Suit API",
    description="A comprehensive social media management platform with enhanced security",
    version="2.0.0",
    docs_url="/docs" if not security_settings.cors_allow_origins else None,  # Disable docs in production
    redoc_url="/redoc" if not security_settings.cors_allow_origins else None
)

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

# -------------------------------
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



