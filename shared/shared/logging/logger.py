"""Logging configuration utilities.

This module provides utilities for configuring logging.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union


class JsonFormatter(logging.Formatter):
    """JSON formatter for logging.
    
    This formatter outputs log records as JSON objects.
    """
    
    def __init__(self, include_timestamp: bool = True):
        """Initialize the formatter.
        
        Args:
            include_timestamp: Whether to include a timestamp in the log
        """
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            A JSON string representation of the log record
        """
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Include any extra attributes
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            }:
                log_data[key] = value
        
        return json.dumps(log_data)


def setup_logger(
    name: str,
    level: Union[int, str] = logging.INFO,
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up a logger with the specified configuration.
    
    Args:
        name: The name of the logger
        level: The logging level
        json_format: Whether to use JSON formatting
        log_file: Optional file path to write logs to
        
    Returns:
        A configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Set formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger by name.
    
    If the logger doesn't exist, it will be created with default settings.
    
    Args:
        name: The name of the logger
        
    Returns:
        A logger instance
    """
    logger = logging.getLogger(name)
    
    # If the logger has no handlers, set up a default one
    if not logger.handlers:
        return setup_logger(name)
    
    return logger