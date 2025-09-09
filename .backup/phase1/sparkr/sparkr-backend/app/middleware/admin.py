from fastapi import Request, HTTPException, status
from typing import Callable, Awaitable


async def admin_middleware(request: Request, call_next: Callable[[Request], Awaitable]):
    """
    Middleware to check for admin header
    For MVP, we're using a simple header check
    In production, this should be replaced with proper role-based authentication
    """
    # Check for admin header
    if request.url.path.startswith("/api/sparkr/admin"):
        admin_header = request.headers.get("X-ADMIN")
        if not admin_header or admin_header.lower() != "true":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    # Continue processing the request
    response = await call_next(request)
    return response