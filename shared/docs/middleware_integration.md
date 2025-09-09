# Middleware Integration Guide

This guide explains how to integrate the shared middleware components into your FastAPI applications.

## Overview

The shared middleware package provides the following components:

1. **Rate Limiting** - Prevents abuse by limiting request rates
2. **Request Logging** - Logs HTTP requests and responses
3. **Correlation ID Tracking** - Adds unique IDs to track requests across services
4. **Health Check Endpoints** - Provides `/healthz` and `/readyz` endpoints
5. **Structured Logging** - Formats logs for Kibana/Grafana

## Installation

The middleware components are part of the shared package. Make sure it's installed in your project.

## Basic Integration

Here's a minimal example of integrating all middleware components:

```python
import os
import redis.asyncio as redis
from fastapi import FastAPI

from shared.middleware import (
    RateLimiter, RateLimitConfig,
    RequestLoggingMiddleware,
    CorrelationIDMiddleware,
    HealthCheckConfig, setup_health_endpoints
)
from shared.logging.structured import setup_structured_logging

# Configure structured logging
setup_structured_logging(
    service_name="your-service-name",
    environment=os.getenv("ENVIRONMENT", "development"),
)

# Create FastAPI app
app = FastAPI()

# Configure Redis for rate limiting
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Configure rate limiting
rate_limit_config = RateLimitConfig(
    default_rate_limit=100,  # 100 requests per minute by default
    path_specific_limits={},  # Add path-specific limits if needed
    redis_key_prefix="your-app:",
)

# Add middleware (order matters)
# 1. Correlation ID middleware (should be first)
app.add_middleware(CorrelationIDMiddleware)

# 2. Request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=True,
    log_response_body=True,
    exclude_paths=["/healthz", "/readyz"],
)

# 3. Rate limiting middleware
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
)
setup_health_endpoints(app, health_config)
```

## Detailed Configuration

### Rate Limiting

The rate limiter uses Redis to track request counts. Configure it with:

```python
rate_limit_config = RateLimitConfig(
    default_rate_limit=100,  # Default requests per minute
    path_specific_limits={
        "/api/limited": 5,  # 5 requests per minute for this endpoint
        "/api/users": 20,  # 20 requests per minute for this endpoint
    },
    redis_key_prefix="your-app:",  # Prefix for Redis keys
    window_size=60,  # Window size in seconds (default: 60)
    block_duration=0,  # How long to block after limit is reached (default: 0 = until window resets)
)

app.add_middleware(
    RateLimiter,
    redis_client=redis_client,
    config=rate_limit_config,
    key_func=None,  # Optional custom function to generate rate limit keys
)
```

### Request Logging

The request logger middleware logs HTTP requests and responses:

```python
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=True,  # Log request bodies
    log_response_body=True,  # Log response bodies
    exclude_paths=["/healthz", "/readyz", "/metrics"],  # Paths to exclude from logging
    exclude_methods=["OPTIONS"],  # Methods to exclude from logging
    sensitive_headers=["Authorization", "Cookie"],  # Headers to mask in logs
    log_level=logging.INFO,  # Log level for requests
    error_log_level=logging.ERROR,  # Log level for error responses
)
```

### Correlation ID

The correlation ID middleware adds a unique ID to each request:

```python
app.add_middleware(
    CorrelationIDMiddleware,
    header_name="X-Correlation-ID",  # Header name (default: X-Correlation-ID)
    include_in_response=True,  # Include ID in response headers (default: True)
    generate_if_not_present=True,  # Generate ID if not in request (default: True)
)
```

To access the correlation ID in your code:

```python
from fastapi import Request
from shared.middleware import get_correlation_id

@app.get("/api/example")
async def example_endpoint(request: Request):
    correlation_id = get_correlation_id(request)
    # Use correlation_id in logs or responses
```

### Health Check Endpoints

The health check endpoints provide `/healthz` and `/readyz` endpoints:

```python
from shared.middleware import HealthCheckConfig, setup_health_endpoints, HealthStatus

# Define custom health checks
async def check_database():
    try:
        # Check database connection
        return True, "Database connection OK"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

async def check_redis():
    try:
        # Check Redis connection
        return True, "Redis connection OK"
    except Exception as e:
        return False, f"Redis connection failed: {str(e)}"

# Configure health checks
health_config = HealthCheckConfig(
    app_version="1.0.0",
    liveness_path="/healthz",
    readiness_path="/readyz",
    liveness_checks=[],  # Liveness checks (basic app functionality)
    readiness_checks=[check_database, check_redis],  # Readiness checks (dependencies)
)

# Setup health check endpoints
setup_health_endpoints(app, health_config)
```

### Structured Logging

Configure structured logging for Kibana/Grafana:

```python
from shared.logging.structured import setup_structured_logging, get_structured_logger

# Configure structured logging
setup_structured_logging(
    service_name="your-service-name",
    environment=os.getenv("ENVIRONMENT", "development"),
    log_level=logging.INFO,
    output=None,  # None = stdout, or provide a file path
)

# Get a structured logger
logger = get_structured_logger("your-module-name")

# Log with context
logger.info("Processing request", extra={"user_id": user_id, "request_id": request_id})

# Log with correlation ID
from fastapi import Request
from shared.middleware import get_correlation_id

@app.get("/api/example")
async def example_endpoint(request: Request):
    correlation_id = get_correlation_id(request)
    logger.info(
        "Processing request",
        extra={"correlation_id": correlation_id, "endpoint": "/api/example"}
    )
```

## Integration Order

The order of middleware is important. The recommended order is:

1. **Correlation ID Middleware** - Should be first to ensure all logs have the correlation ID
2. **Request Logging Middleware** - Should be early to capture all requests
3. **Rate Limiting Middleware** - After logging but before processing
4. **Other Application-Specific Middleware**

## Environment Variables

The middleware components use the following environment variables:

- `REDIS_URL` - Redis connection URL for rate limiting (default: `redis://localhost:6379/0`)
- `ENVIRONMENT` - Environment name for logging (default: `development`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

## Kubernetes Integration

The health check endpoints are designed to work with Kubernetes:

```yaml
# In your Kubernetes deployment
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /readyz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Complete Example

See the `middleware_example.py` file in the `shared/examples` directory for a complete example of all middleware components working together.