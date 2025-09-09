"""Logging utilities for shared projects.

This module provides common logging functionality including logger configuration,
formatters, handlers, and structured logging with Kibana/Grafana support.
"""

# Import key components to make them available when importing the logging module
from shared.logging.config import setup_logger, get_logger
from shared.logging.formatters import JsonFormatter
from shared.logging.structured import (
    StructuredLogFormatter,
    setup_structured_logging,
    StructuredLogger,
    get_structured_logger,
)