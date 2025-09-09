"""Example application demonstrating the use of shared middleware components.

This example shows how to use rate limiting, request logging, correlation ID tracking,
and health check endpoints in a FastAPI application.
"""

import os
import logging
from typing import Dict, Any

import redis.asyncio as redis
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse

from shared.middleware import (
    RateLimiter, RateLimitConfig,
    RequestLoggingMiddleware,
    CorrelationIDMiddleware, get_correlation_id,
    HealthCheckConfig, setup_health_endpoints, HealthStatus
)
from shared.logging.structured import setup_structured_logging, get_structured_logger

# Configure structured logging
setup_structured_logging(
    service_name="middleware-example",
    environment="development",
    log_level=logging.INFO,
)

# Create a structured logger
logger = get_structured_logger("middleware-example")

# Create FastAPI app
app = FastAPI(title="Middleware Example")

# Configure Redis for rate limiting
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)

# Configure rate limiting
rate_limit_config = RateLimitConfig(
    default_rate_limit=100,  # 100 requests per minute by default
    path_specific_limits={
        "/api/limited": 5,  # 5 requests per minute for this endpoint
    },
    redis_key_prefix="example-app:",
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Add request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=True,
    log_response_body=True,
    exclude_paths=["/healthz", "/readyz"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimiter,
    redis_client=redis_client,
    config=rate_limit_config,
)

# Setup health check endpoints
health_config = HealthCheckConfig(
    app_version="1.0.0",
    liveness_path="/healthz",
    readiness_path="/readyz",
    liveness_checks=[],  # Add custom liveness checks if needed
    readiness_checks=[],  # Add custom readiness checks if needed
)
setup_health_endpoints(app, health_config)


# Example endpoint that uses correlation ID
@app.get("/api/example")
async def example_endpoint(request: Request):
    # Get correlation ID from request
    correlation_id = get_correlation_id(request)
    
    # Log with correlation ID
    logger.info(
        "Processing request",
        extra={"correlation_id": correlation_id, "endpoint": "/api/example"}
    )
    
    # Return response with correlation ID
    return {
        "message": "Hello, World!",
        "correlation_id": correlation_id,
    }


# Example rate-limited endpoint
@app.get("/api/limited")
async def limited_endpoint(request: Request):
    correlation_id = get_correlation_id(request)
    logger.info(
        "Processing rate-limited request",
        extra={"correlation_id": correlation_id, "endpoint": "/api/limited"}
    )
    return {"message": "This endpoint is rate-limited to 5 requests per minute"}


# Example endpoint that simulates an error
@app.get("/api/error")
async def error_endpoint(request: Request):
    correlation_id = get_correlation_id(request)
    logger.error(
        "Simulated error occurred",
        extra={
            "correlation_id": correlation_id,
            "endpoint": "/api/error",
            "error_type": "SimulatedError",
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Simulated error",
            "correlation_id": correlation_id,
        },
    )


# Example of how to run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("middleware_example:app", host="0.0.0.0", port=8000, reload=True)