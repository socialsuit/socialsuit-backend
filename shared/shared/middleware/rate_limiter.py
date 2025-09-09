"""Rate limiting middleware for FastAPI applications.

This module provides a configurable rate limiter middleware for FastAPI.
"""

from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis.asyncio as redis


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    limit: int
    window_seconds: int
    key_func: Optional[Callable[[Request], str]] = None


class RateLimiter:
    """Rate limiter middleware for FastAPI.
    
    This middleware limits the number of requests a client can make within
    a specified time window.
    """
    
    def __init__(
        self,
        redis_url: str,
        default_limit: int = 100,
        default_window_seconds: int = 60,
        path_configs: Optional[Dict[str, RateLimitConfig]] = None,
    ):
        """Initialize the rate limiter.
        
        Args:
            redis_url: The Redis connection URL
            default_limit: The default request limit
            default_window_seconds: The default time window in seconds
            path_configs: Optional path-specific configurations
        """
        self.redis_url = redis_url
        self.default_limit = default_limit
        self.default_window_seconds = default_window_seconds
        self.path_configs = path_configs or {}
        self.redis_pool = None
    
    async def init_redis_pool(self):
        """Initialize the Redis connection pool."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(self.redis_url)
    
    def get_config_for_path(self, path: str) -> RateLimitConfig:
        """Get the rate limit configuration for a path.
        
        Args:
            path: The request path
            
        Returns:
            The rate limit configuration for the path
        """
        # Check for exact path match
        if path in self.path_configs:
            return self.path_configs[path]
        
        # Check for path prefix matches
        for config_path, config in self.path_configs.items():
            if config_path.endswith('*') and path.startswith(config_path[:-1]):
                return config
        
        # Use default configuration
        return RateLimitConfig(
            limit=self.default_limit,
            window_seconds=self.default_window_seconds
        )
    
    def get_key_for_request(self, request: Request, config: RateLimitConfig) -> str:
        """Get the rate limit key for a request.
        
        Args:
            request: The FastAPI request
            config: The rate limit configuration
            
        Returns:
            The rate limit key
        """
        if config.key_func:
            return config.key_func(request)
        
        # Default to IP-based rate limiting
        client_ip = request.client.host if request.client else "unknown"
        return f"ratelimit:{client_ip}:{request.url.path}"
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the rate limiter.
        
        Args:
            request: The FastAPI request
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        await self.init_redis_pool()
        
        # Skip rate limiting for certain paths
        if request.url.path in ["/healthz", "/ping", "/metrics"]:
            return await call_next(request)
        
        # Get configuration for this path
        config = self.get_config_for_path(request.url.path)
        
        # Get rate limit key
        key = self.get_key_for_request(request, config)
        
        # Check rate limit
        async with redis.Redis.from_pool(self.redis_pool) as r:
            # Get current count
            count = await r.get(key)
            count = int(count) if count else 0
            
            # Check if limit exceeded
            if count >= config.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "limit": config.limit,
                        "window_seconds": config.window_seconds,
                    }
                )
            
            # Increment count and set expiry if needed
            pipe = r.pipeline()
            pipe.incr(key)
            if count == 0:
                pipe.expire(key, config.window_seconds)
            await pipe.execute()
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(config.limit)
        response.headers["X-RateLimit-Remaining"] = str(config.limit - count - 1)
        
        return response


def add_rate_limiter(
    app: FastAPI,
    redis_url: str,
    default_limit: int = 100,
    default_window_seconds: int = 60,
    path_configs: Optional[Dict[str, RateLimitConfig]] = None,
) -> None:
    """Add rate limiting middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application
        redis_url: The Redis connection URL
        default_limit: The default request limit
        default_window_seconds: The default time window in seconds
        path_configs: Optional path-specific configurations
    """
    limiter = RateLimiter(
        redis_url=redis_url,
        default_limit=default_limit,
        default_window_seconds=default_window_seconds,
        path_configs=path_configs,
    )
    
    app.add_middleware(limiter)