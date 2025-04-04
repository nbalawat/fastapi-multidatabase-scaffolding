import logging
import sys
from typing import Any, Dict, List

import structlog
from structlog.types import Processor

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure logging for the application.
    
    Args:
        settings: Application settings containing logging configuration
    """
    # Set the log level
    log_level = getattr(logging, settings.log_level)
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )
    
    # Define processors for structlog
    processors: List[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Add JSON formatting in production, human-readable in debug
    if settings.debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger for the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A structlog logger
    """
    return structlog.get_logger(name)
