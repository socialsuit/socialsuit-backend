"""Request logging middleware for FastAPI applications.

This module provides middleware for logging HTTP requests and responses.
"""

import time
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
import logging

from shared.logging.logger import get_logger


class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests and responses.
    
    This middleware logs information about incoming requests and outgoing responses,
    including timing information.
    """
    
    def __init__(
        self,
        app: FastAPI,
        logger: Optional[logging.Logger] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: list[str] = None,
    ):
        """Initialize the middleware.
        
        Args:
            app: The FastAPI application
            logger: Optional logger to use (defaults to 'request_logger')
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            exclude_paths: List of paths to exclude from logging
        """
        self.app = app
        self.logger = logger or get_logger("request_logger")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or ["/healthz", "/ping", "/metrics"]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: The FastAPI request
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request)
        
        # Process request
        try:
            response = await call_next(request)
            # Log response
            self._log_response(request, response, start_time)
            return response
        except Exception as e:
            # Log exception
            self.logger.exception(
                f"Error processing request: {request.method} {request.url.path}"
            )
            raise
    
    async def _log_request(self, request: Request) -> None:
        """Log information about the request.
        
        Args:
            request: The FastAPI request
        """
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        log_data = {
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_agent": user_agent,
        }
        
        # Log request headers
        log_data["headers"] = dict(request.headers)
        
        # Log request body if enabled
        if self.log_request_body:
            try:
                body = await request.body()
                if body:
                    log_data["body"] = body.decode()
            except Exception as e:
                log_data["body_error"] = str(e)
        
        self.logger.info(f"Request: {request.method} {request.url.path}", extra=log_data)
    
    def _log_response(self, request: Request, response: Response, start_time: float) -> None:
        """Log information about the response.
        
        Args:
            request: The FastAPI request
            response: The FastAPI response
            start_time: The time the request was received
        """
        process_time = time.time() - start_time
        status_code = response.status_code
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "response_headers": dict(response.headers),
        }
        
        # Log response body if enabled
        if self.log_response_body:
            try:
                # This is a bit tricky as the response body might have been consumed
                # We can only log the response body if it's available
                if hasattr(response, "body"):
                    log_data["body"] = response.body.decode()
            except Exception as e:
                log_data["body_error"] = str(e)
        
        log_level = logging.INFO
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        
        self.logger.log(
            log_level,
            f"Response: {request.method} {request.url.path} {status_code} ({process_time:.2f}s)",
            extra=log_data
        )


def add_request_logger(
    app: FastAPI,
    logger: Optional[logging.Logger] = None,
    log_request_body: bool = False,
    log_response_body: bool = False,
    exclude_paths: list[str] = None,
) -> None:
    """Add request logging middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application
        logger: Optional logger to use
        log_request_body: Whether to log request bodies
        log_response_body: Whether to log response bodies
        exclude_paths: List of paths to exclude from logging
    """
    middleware = RequestLoggingMiddleware(
        app=app,
        logger=logger,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        exclude_paths=exclude_paths,
    )
    
    app.add_middleware(middleware.__class__, middleware=middleware)