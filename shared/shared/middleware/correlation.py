"""Correlation ID middleware for FastAPI applications.

This module provides middleware for adding correlation IDs to requests and responses.
"""

import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
import logging

from shared.logging.logger import get_logger


class CorrelationIDMiddleware:
    """Middleware for adding correlation IDs to requests and responses.
    
    This middleware ensures that each request has a unique correlation ID that can be
    used to trace the request across multiple services and in logs.
    """
    
    def __init__(
        self,
        app: FastAPI,
        header_name: str = "X-Correlation-ID",
        context_key: str = "correlation_id",
        generator: Callable[[], str] = lambda: str(uuid.uuid4()),
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the middleware.
        
        Args:
            app: The FastAPI application
            header_name: The name of the header to use for the correlation ID
            context_key: The key to use in the request state for the correlation ID
            generator: A function that generates correlation IDs
            logger: Optional logger to use (defaults to 'correlation_logger')
        """
        self.app = app
        self.header_name = header_name
        self.context_key = context_key
        self.generator = generator
        self.logger = logger or get_logger("correlation_logger")
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process the request through the middleware.
        
        Args:
            request: The FastAPI request
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(self.header_name)
        if not correlation_id:
            correlation_id = self.generator()
        
        # Store correlation ID in request state
        request.state.__dict__[self.context_key] = correlation_id
        
        # Add correlation ID to logging context
        logger = logging.getLogger()
        old_factory = logger.makeRecord
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.correlation_id = correlation_id
            return record
        
        logger.makeRecord = record_factory
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add correlation ID to response headers
            response.headers[self.header_name] = correlation_id
            
            return response
        finally:
            # Restore original record factory
            logger.makeRecord = old_factory


def get_correlation_id(request: Request, context_key: str = "correlation_id") -> Optional[str]:
    """Get the correlation ID from the request state.
    
    Args:
        request: The FastAPI request
        context_key: The key used in the request state for the correlation ID
        
    Returns:
        The correlation ID if available, None otherwise
    """
    return getattr(request.state, context_key, None)