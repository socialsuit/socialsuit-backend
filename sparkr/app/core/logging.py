import logging
import sys
from typing import Any, Dict, List, Optional

import sentry_sdk
from loguru import logger
from pydantic import BaseModel

from sparkr.app.core.config import settings


class LogConfig(BaseModel):
    """Logging configuration"""
    
    LOGGER_NAME: str = "sparkr"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_LEVEL: str = "DEBUG" if settings.DEBUG else "INFO"
    
    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: Dict[str, Dict[str, str]] = {
        "default": {
            "format": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers: Dict[str, Dict[str, Any]] = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers: Dict[str, Dict[str, Any]] = {
        LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
    }


# Configure loguru logger
log_config = LogConfig()


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru"""
    
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_sentry():
    """Initialize Sentry SDK for error tracking"""
    sentry_dsn = os.getenv("SENTRY_DSN", "")
    
    if not sentry_dsn:
        logger.warning("Sentry DSN not provided. Sentry integration disabled.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.2,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.1,
        environment="production" if not settings.DEBUG else "development",
        release=settings.VERSION,
    )
    logger.info("Sentry integration initialized successfully.")


def setup_logging() -> None:
    """Configure logging with loguru and initialize Sentry"""
    # Initialize Sentry
    setup_sentry()
    
    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_config.LOG_LEVEL)
    
    # Remove every other logger's handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
        
    # Configure loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "format": log_config.LOG_FORMAT,
                "level": log_config.LOG_LEVEL,
            }
        ]
    )