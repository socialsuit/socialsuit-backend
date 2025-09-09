from typing import Any, Callable, Dict, Optional, Type, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException

from shared.utils.response_envelope import ResponseEnvelope


# Error code prefixes
VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
HTTP_ERROR_CODE = "HTTP_ERROR"
SERVER_ERROR_CODE = "SERVER_ERROR"


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and return a standardized error response.
    
    Args:
        request: The incoming request
        exc: The HTTPException that was raised
        
    Returns:
        A JSONResponse with the standardized error format
    """
    error_code = f"{HTTP_ERROR_CODE}_{exc.status_code}"
    return JSONResponse(
        status_code=exc.status_code,
        content=ResponseEnvelope.error_response(
            code=error_code,
            message=exc.detail,
            details={"headers": exc.headers} if exc.headers else None
        ).dict(exclude_none=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle RequestValidationError and return a standardized error response.
    
    Args:
        request: The incoming request
        exc: The RequestValidationError that was raised
        
    Returns:
        A JSONResponse with the standardized error format
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseEnvelope.error_response(
            code=VALIDATION_ERROR_CODE,
            message="Request validation error",
            details={"errors": exc.errors()}
        ).dict(exclude_none=True)
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError and return a standardized error response.
    
    Args:
        request: The incoming request
        exc: The ValidationError that was raised
        
    Returns:
        A JSONResponse with the standardized error format
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ResponseEnvelope.error_response(
            code=VALIDATION_ERROR_CODE,
            message="Data validation error",
            details={"errors": exc.errors()}
        ).dict(exclude_none=True)
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions and return a standardized error response.
    
    Args:
        request: The incoming request
        exc: The unhandled exception that was raised
        
    Returns:
        A JSONResponse with the standardized error format
    """
    # In production, you would want to log the exception here
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseEnvelope.error_response(
            code=SERVER_ERROR_CODE,
            message="An unexpected error occurred",
            # In production, you might not want to expose the exception details
            details={"type": exc.__class__.__name__, "message": str(exc)}
        ).dict(exclude_none=True)
    )