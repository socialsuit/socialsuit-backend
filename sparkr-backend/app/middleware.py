"""Middleware configuration for the Sparkr backend application.

This module sets up all middleware components for the application, including
rate limiting, request logging, correlation ID tracking, and health checks.
"""

import os
import logging
from typing import Callable

import redis.asyncio as redis
from fastapi import FastAPI

from shared.middleware import (
    RateLimiter, RateLimitConfig,
    RequestLoggingMiddleware,
    CorrelationIDMiddleware,
    HealthCheckConfig, setup_health_endpoints
)
from shared.logging.structured import setup_structured_logging


def setup_middleware(app: FastAPI) -> None:
    """Set up all middleware components for the application.
    
    Args:
        app: The FastAPI application
    """
    # Configure structured logging
    setup_structured_logging(
        service_name="sparkr-backend",
        environment=os.getenv("ENVIRONMENT", "development"),
        log_level=logging.INFO,
    )
    
    # Configure Redis for rate limiting
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url)
    
    # Configure rate limiting
    rate_limit_config = RateLimitConfig(
        default_rate_limit=100,  # 100 requests per minute by default
        path_specific_limits={
            "/api/users": 30,  # 30 requests per minute
            "/api/auth/login": 10,  # 10 requests per minute
        },
        redis_key_prefix="sparkr:",
    )
    
    # Add correlation ID middleware (should be first)
    app.add_middleware(CorrelationIDMiddleware)
    
    # Add request logging middleware
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=True,
        log_response_body=True,
        exclude_paths=["/healthz", "/readyz", "/metrics"],
    )
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimiter,
        redis_client=redis_client,
        config=rate_limit_config,
    )
    
    # Setup health check endpoints
    setup_health_endpoints(
        app,
        HealthCheckConfig(
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            liveness_path="/healthz",
            readiness_path="/readyz",
            liveness_checks=[],  # Add custom liveness checks if needed
            readiness_checks=[check_database_connection, check_redis_connection],
        )
    )


async def check_database_connection() -> tuple[bool, str]:
    """Check if the database connection is healthy.
    
    Returns:
        A tuple of (is_healthy, message)
    """
    try:
        # This is a placeholder - in a real application, you would
        # check the actual database connection here
        # For example:
        # from app.database import engine
        # async with engine.connect() as conn:
        #     await conn.execute("SELECT 1")
        return True, "Database connection is healthy"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


async def check_redis_connection() -> tuple[bool, str]:
    """Check if the Redis connection is healthy.
    
    Returns:
        A tuple of (is_healthy, message)
    """
    try:
        # This is a placeholder - in a real application, you would
        # check the actual Redis connection here
        # For example:
        # redis_client = redis.from_url(os.getenv("REDIS_URL"))
        # await redis_client.ping()
        return True, "Redis connection is healthy"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"