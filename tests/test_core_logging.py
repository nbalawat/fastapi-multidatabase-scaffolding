import logging
from unittest.mock import patch, MagicMock

import pytest
import structlog

from app.core.config import Settings
from app.core.logging import configure_logging, get_logger


def test_configure_logging():
    """Test that logging is configured correctly."""
    # Mock settings
    settings = Settings(log_level="INFO")
    
    # Configure logging
    with patch("structlog.configure") as mock_configure:
        configure_logging(settings)
        
        # Verify that structlog.configure was called
        mock_configure.assert_called_once()


def test_get_logger():
    """Test that get_logger returns a logger."""
    # Get a logger
    logger = get_logger("test")
    
    # Verify that it's a structlog logger
    assert isinstance(logger, structlog.stdlib.BoundLogger)


def test_logger_levels():
    """Test that the logger respects log levels."""
    # Mock a processor
    mock_processor = MagicMock()
    
    # Configure structlog with our mock processor
    structlog.configure(
        processors=[mock_processor],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    # Get a logger
    logger = get_logger("test_levels")
    
    # Set the log level to INFO
    logging.getLogger("test_levels").setLevel(logging.INFO)
    
    # Log at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Verify that debug message was not processed (due to INFO level)
    assert mock_processor.call_count == 3
    
    # Reset the mock
    mock_processor.reset_mock()
    
    # Set the log level to DEBUG
    logging.getLogger("test_levels").setLevel(logging.DEBUG)
    
    # Log at different levels again
    logger.debug("Debug message")
    logger.info("Info message")
    
    # Verify that both messages were processed
    assert mock_processor.call_count == 2
