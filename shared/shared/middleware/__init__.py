"""Middleware components for shared projects.

This module provides common middleware functionality including rate limiting,
request logging, correlation ID tracking, health check endpoints, and security middleware.
"""

# Import key components to make them available when importing the middleware module
from shared.middleware.rate_limiter import RateLimiter, RateLimitConfig
from shared.middleware.request_logger import RequestLoggingMiddleware
from shared.middleware.correlation import CorrelationIDMiddleware, get_correlation_id
from shared.middleware.health import HealthCheckConfig, setup_health_endpoints, HealthStatus