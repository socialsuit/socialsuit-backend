import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from loguru import logger


async def request_logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    """Middleware to log request information"""
    # Generate a unique request ID
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    
    # Log request details
    logger.info(f"[{request_id}] Request: {request.method} {request.url.path} - Client: {request.client.host}")
    
    # Record request start time
    start_time = time.time()
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(
            f"[{request_id}] Response: {response.status_code} - "
            f"Completed in {process_time:.4f}s"
        )
        
        # Add processing time header to response
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response
    except Exception as e:
        # Log any exceptions that occur during request processing
        logger.error(f"[{request_id}] Error processing request: {str(e)}")
        raise