from fastapi import Request, HTTPException, status
from typing import Dict, Optional, Callable, Any, Union
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API endpoints.
    
    Supports different rate limiting strategies:
    - Fixed window: Limits requests in fixed time windows
    - Sliding window: Uses a moving time window for more accurate limiting
    - Token bucket: Allows for bursts of traffic while maintaining average rate
    """
    
    STRATEGY_FIXED_WINDOW = "fixed_window"
    STRATEGY_SLIDING_WINDOW = "sliding_window"
    STRATEGY_TOKEN_BUCKET = "token_bucket"
    
    def __init__(
        self,
        rate_limit: int = 100,  # Default: 100 requests
        time_window: int = 60,  # Default: per 60 seconds (1 minute)
        strategy: str = STRATEGY_FIXED_WINDOW,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list] = None,
        burst_limit: Optional[int] = None,  # For token bucket strategy
        storage_backend: Optional[Any] = None  # For distributed rate limiting
    ):
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.strategy = strategy
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or []
        self.burst_limit = burst_limit or rate_limit
        self.storage_backend = storage_backend
        
        # In-memory storage for rate limiting data
        self._request_counts: Dict[str, Dict[str, Union[int, float, list]]] = {}
        self._lock = asyncio.Lock()
    
    def _default_key_func(self, request: Request) -> str:
        """Default function to generate a key for rate limiting.
        
        Uses client IP by default. Override this for custom rate limiting strategies.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        return f"{ip}"
    
    def _is_path_excluded(self, request: Request) -> bool:
        """Check if the request path is excluded from rate limiting."""
        path = request.url.path
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check if a request exceeds the rate limit.
        
        Raises HTTPException if rate limit is exceeded.
        """
        if self._is_path_excluded(request):
            return
        
        key = self.key_func(request)
        current_time = time.time()
        
        # Use external storage if provided
        if self.storage_backend:
            return await self._check_rate_limit_external(key, current_time, request)
        
        # Otherwise use in-memory implementation
        async with self._lock:
            if self.strategy == self.STRATEGY_FIXED_WINDOW:
                await self._check_fixed_window(key, current_time)
            elif self.strategy == self.STRATEGY_SLIDING_WINDOW:
                await self._check_sliding_window(key, current_time)
            elif self.strategy == self.STRATEGY_TOKEN_BUCKET:
                await self._check_token_bucket(key, current_time)
            else:
                # Default to fixed window if strategy is unknown
                await self._check_fixed_window(key, current_time)
    
    async def _check_fixed_window(self, key: str, current_time: float) -> None:
        """Fixed window rate limiting strategy."""
        # Get or create window data
        if key not in self._request_counts:
            self._request_counts[key] = {
                "count": 1,
                "window_start": current_time
            }
            return
        
        window_data = self._request_counts[key]
        window_start = window_data["window_start"]
        
        # If current window has expired, start a new one
        if current_time - window_start > self.time_window:
            window_data["count"] = 1
            window_data["window_start"] = current_time
            return
        
        # Otherwise increment the counter
        window_data["count"] += 1
        
        # Check if rate limit is exceeded
        if window_data["count"] > self.rate_limit:
            reset_time = window_start + self.time_window
            retry_after = int(reset_time - current_time)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
    
    async def _check_sliding_window(self, key: str, current_time: float) -> None:
        """Sliding window rate limiting strategy."""
        # Get or create window data
        if key not in self._request_counts:
            self._request_counts[key] = {
                "requests": [(current_time, 1)],
                "count": 1
            }
            return
        
        window_data = self._request_counts[key]
        requests = window_data["requests"]
        
        # Remove requests outside the time window
        cutoff_time = current_time - self.time_window
        valid_requests = [(t, c) for t, c in requests if t >= cutoff_time]
        
        # Add current request
        valid_requests.append((current_time, 1))
        
        # Update window data
        window_data["requests"] = valid_requests
        window_data["count"] = sum(count for _, count in valid_requests)
        
        # Check if rate limit is exceeded
        if window_data["count"] > self.rate_limit:
            # Calculate retry-after as the time until the oldest request expires
            oldest_time = valid_requests[0][0]
            retry_after = int(oldest_time + self.time_window - current_time)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
    
    async def _check_token_bucket(self, key: str, current_time: float) -> None:
        """Token bucket rate limiting strategy."""
        # Get or create bucket data
        if key not in self._request_counts:
            self._request_counts[key] = {
                "tokens": self.burst_limit - 1,  # Use one token for this request
                "last_refill": current_time
            }
            return
        
        bucket = self._request_counts[key]
        
        # Calculate token refill
        time_passed = current_time - bucket["last_refill"]
        token_refill = time_passed * (self.rate_limit / self.time_window)
        
        # Refill the bucket (up to burst limit)
        new_token_count = min(bucket["tokens"] + token_refill, self.burst_limit)
        
        # Check if we have enough tokens
        if new_token_count < 1:
            # Calculate time until next token is available
            time_per_token = self.time_window / self.rate_limit
            tokens_needed = 1 - new_token_count
            retry_after = int(tokens_needed * time_per_token)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Use one token and update bucket
        bucket["tokens"] = new_token_count - 1
        bucket["last_refill"] = current_time
    
    async def _check_rate_limit_external(self, key: str, current_time: float, request: Request) -> None:
        """Use external storage backend for rate limiting."""
        if not self.storage_backend:
            return
        
        try:
            # Delegate rate limiting to external storage
            result = await self.storage_backend.check_rate_limit(
                key=key,
                current_time=current_time,
                rate_limit=self.rate_limit,
                time_window=self.time_window,
                strategy=self.strategy,
                burst_limit=self.burst_limit,
                request=request
            )
            
            # If result contains retry_after, rate limit is exceeded
            if result and "retry_after" in result:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {result['retry_after']} seconds.",
                    headers={"Retry-After": str(result["retry_after"])}
                )
                
        except Exception as e:
            # Log error but don't block request if rate limiting fails
            logger.error(f"Error in external rate limiting: {str(e)}")
            # Optionally, you could raise the exception here if you want to fail closed
            # rather than fail open when the rate limiter has an error