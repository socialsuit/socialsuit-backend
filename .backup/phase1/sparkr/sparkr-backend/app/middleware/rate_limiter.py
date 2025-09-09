import time
from typing import Dict, Tuple, Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from loguru import logger
from app.core.config import settings


# Simple in-memory store for rate limiting
# In production, consider using Redis for distributed rate limiting
class RateLimiter:
    def __init__(self, rate_limit: int = 100, window: int = 60):
        """Initialize rate limiter
        
        Args:
            rate_limit: Maximum number of requests allowed in the time window
            window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.window = window
        self.clients: Dict[str, Tuple[int, float]] = {}  # {ip: (count, start_time)}
    
    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited"""
        current_time = time.time()
        
        # If client not in store or window has expired, reset
        if client_ip not in self.clients or current_time - self.clients[client_ip][1] > self.window:
            self.clients[client_ip] = (1, current_time)
            return False
        
        # Get current count and start time
        count, start_time = self.clients[client_ip]
        
        # Check if rate limit exceeded
        if count >= self.rate_limit:
            return True
        
        # Increment count
        self.clients[client_ip] = (count + 1, start_time)
        return False


# Create rate limiter instance
rate_limiter = RateLimiter(
    rate_limit=int(os.getenv("RATE_LIMIT", "100")),
    window=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
)


async def rate_limiting_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    """Middleware to implement rate limiting"""
    # Skip rate limiting for certain paths
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host
    
    # Check if client is rate limited
    if rate_limiter.is_rate_limited(client_ip):
        logger.warning(f"Rate limit exceeded for client: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Process the request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(rate_limiter.rate_limit)
    response.headers["X-RateLimit-Remaining"] = str(
        rate_limiter.rate_limit - rate_limiter.clients.get(client_ip, (0, 0))[0]
    )
    
    return response