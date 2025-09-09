from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi import Response
from fastapi.responses import JSONResponse

from shared.utils.response_envelope import ResponseEnvelope

# Type variable for the route handler function
F = TypeVar('F', bound=Callable[..., Any])


def envelope_response(func: F) -> F:
    """Decorator to wrap FastAPI route responses in the standard ResponseEnvelope.
    
    This decorator automatically wraps the return value of a FastAPI route handler
    in a ResponseEnvelope with success=True. If the handler returns a Response object
    (like JSONResponse, HTMLResponse, etc.), it passes it through unchanged.
    
    Args:
        func: The FastAPI route handler function to wrap
        
    Returns:
        The wrapped function that returns a ResponseEnvelope
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = await func(*args, **kwargs) if callable(func) else func
        
        # If the result is already a Response object, return it as is
        if isinstance(result, Response):
            return result
        
        # Otherwise, wrap the result in a ResponseEnvelope
        return ResponseEnvelope.success_response(data=result)
    
    return wrapper  # type: ignore


def create_error_response(
    code: str, 
    message: str, 
    status_code: int = 400, 
    details: dict = None
) -> JSONResponse:
    """Create a JSONResponse with an error ResponseEnvelope.
    
    This is a convenience function for creating error responses in route handlers.
    
    Args:
        code: Error code for programmatic handling
        message: Human-readable error message
        status_code: HTTP status code to return
        details: Additional error details
        
    Returns:
        A JSONResponse with the error ResponseEnvelope
    """
    return JSONResponse(
        status_code=status_code,
        content=ResponseEnvelope.error_response(
            code=code,
            message=message,
            details=details
        ).dict(exclude_none=True)
    )