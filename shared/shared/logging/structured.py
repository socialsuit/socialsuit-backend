"""Structured logging utilities for applications.

This module provides utilities for structured logging with support for
Kibana and Grafana formats.
"""

import json
import logging\import sys
from datetime import datetime
from typing import Any, Dict, Optional, Union


class StructuredLogFormatter(logging.Formatter):
    """Formatter for structured JSON logs.
    
    This formatter outputs logs in a structured JSON format that is compatible
    with Kibana and Grafana.
    """
    
    def __init__(
        self,
        service_name: str,
        environment: str,
        include_timestamp: bool = True,
        include_hostname: bool = True,
        include_level_name: bool = True,
    ):
        """Initialize the formatter.
        
        Args:
            service_name: The name of the service
            environment: The environment (e.g., production, staging)
            include_timestamp: Whether to include a timestamp
            include_hostname: Whether to include the hostname
            include_level_name: Whether to include the level name
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_timestamp = include_timestamp
        self.include_hostname = include_hostname
        self.include_level_name = include_level_name
        
        # Get hostname if needed
        self.hostname = None
        if include_hostname:
            import socket
            self.hostname = socket.gethostname()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.
        
        Args:
            record: The log record
            
        Returns:
            A JSON string
        """
        # Base log data
        log_data = {
            "message": record.getMessage(),
            "logger": record.name,
            "service": self.service_name,
            "environment": self.environment,
        }
        
        # Add timestamp
        if self.include_timestamp:
            log_data["@timestamp"] = datetime.utcfromtimestamp(record.created).isoformat() + "Z"
        
        # Add hostname
        if self.include_hostname and self.hostname:
            log_data["host"] = self.hostname
        
        # Add level
        if self.include_level_name:
            log_data["level"] = record.levelname
            log_data["level_number"] = record.levelno
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra attributes from record
        for key, value in record.__dict__.items():
            if key not in [
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName",
                "correlation_id",  # Already handled above
            ]:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_structured_logging(
    service_name: str,
    environment: str,
    log_level: Union[int, str] = logging.INFO,
    output: Optional[str] = None,
) -> None:
    """Set up structured logging for the application.
    
    Args:
        service_name: The name of the service
        environment: The environment (e.g., production, staging)
        log_level: The log level
        output: Optional output file path (defaults to stdout)
    """
    # Create formatter
    formatter = StructuredLogFormatter(
        service_name=service_name,
        environment=environment,
    )
    
    # Create handler
    if output:
        handler = logging.FileHandler(output)
    else:
        handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter on handler
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    
    # Add our handler
    root_logger.addHandler(handler)


class StructuredLogger:
    """Logger that adds structured context to log messages.
    
    This logger allows adding context to log messages that will be included
    in the structured output.
    """
    
    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """Initialize the logger.
        
        Args:
            name: The logger name
            context: Optional initial context
        """
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def with_context(self, **kwargs) -> "StructuredLogger":
        """Create a new logger with additional context.
        
        Args:
            **kwargs: Context key-value pairs
            
        Returns:
            A new logger with the combined context
        """
        new_context = {**self.context, **kwargs}
        return StructuredLogger(self.logger.name, new_context)
    
    def _log(self, level: int, msg: str, *args, **kwargs) -> None:
        """Log a message with the given level.
        
        Args:
            level: The log level
            msg: The message format string
            *args: Format string arguments
            **kwargs: Additional context or logging parameters
        """
        # Extract extra context from kwargs
        extra_context = kwargs.pop("extra", {})
        
        # Combine context
        context = {**self.context, **extra_context}
        
        # Log with context
        self.logger.log(level, msg, *args, extra=context, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message."""
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message."""
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs) -> None:
        """Log an exception message."""
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self._log(logging.ERROR, msg, *args, **kwargs)


def get_structured_logger(name: str, context: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """Get a structured logger.
    
    Args:
        name: The logger name
        context: Optional initial context
        
    Returns:
        A structured logger
    """
    return StructuredLogger(name, context)