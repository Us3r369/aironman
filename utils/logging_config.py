"""
Centralized logging configuration for AIronman app.
Provides structured logging with correlation IDs and proper error handling.
"""

import logging
import logging.config
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from pathlib import Path

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        record.correlation_id = correlation_id.get() or 'no-id'
        return True

class StructuredFormatter(logging.Formatter):
    """Structured log formatter with correlation ID and timestamp."""
    
    def format(self, record):
        # Add correlation ID if not present
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = correlation_id.get() or 'no-id'
        
        # Add timestamp if not present
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.utcnow().isoformat()
        
        # Format the message
        return super().format(record)

def get_correlation_id() -> str:
    """Get current correlation ID or generate a new one."""
    current_id = correlation_id.get()
    if not current_id:
        current_id = str(uuid.uuid4())
        correlation_id.set(current_id)
    return current_id

def set_correlation_id(corr_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id.set(corr_id)

def clear_correlation_id() -> None:
    """Clear correlation ID for current context."""
    correlation_id.set(None)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Setup centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    """
    
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'structured': {
                '()': StructuredFormatter,
                'format': '%(timestamp)s [%(correlation_id)s] %(levelname)s %(name)s: %(message)s'
            },
            'simple': {
                'format': '%(levelname)s: %(message)s'
            }
        },
        'filters': {
            'correlation_id': {
                '()': CorrelationIdFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'structured',
                'filters': ['correlation_id'],
                'stream': sys.stdout
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'api': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'services': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'utils': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'sync': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'preprocess': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    # Add file handler if specified
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'level': log_level,
            'formatter': 'structured',
            'filters': ['correlation_id'],
            'filename': log_file
        }
        
        # Add file handler to all loggers
        for logger_config in config['loggers'].values():
            logger_config['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(config)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

class ErrorContext:
    """Context manager for error handling with correlation ID."""
    
    def __init__(self, operation: str, logger: logging.Logger, **context):
        self.operation = operation
        self.logger = logger
        self.context = context
        self.correlation_id = get_correlation_id()
    
    def __enter__(self):
        self.logger.info(
            f"Starting {self.operation}",
            extra={
                'correlation_id': self.correlation_id,
                'operation': self.operation,
                **self.context
            }
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Error in {self.operation}: {exc_val}",
                extra={
                    'correlation_id': self.correlation_id,
                    'operation': self.operation,
                    'error_type': exc_type.__name__,
                    'error_message': str(exc_val),
                    **self.context
                },
                exc_info=True
            )
        else:
            self.logger.info(
                f"Completed {self.operation}",
                extra={
                    'correlation_id': self.correlation_id,
                    'operation': self.operation,
                    **self.context
                }
            )

def log_error(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with structured context.
    
    Args:
        logger: Logger instance
        message: Error message
        error: Exception that occurred
        context: Additional context information
    """
    extra = {
        'correlation_id': get_correlation_id(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        **(context or {})
    }
    
    logger.error(
        f"{message}: {error}",
        extra=extra,
        exc_info=True
    )

def log_warning(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a warning with structured context.
    
    Args:
        logger: Logger instance
        message: Warning message
        context: Additional context information
    """
    extra = {
        'correlation_id': get_correlation_id(),
        **(context or {})
    }
    
    logger.warning(message, extra=extra)

def log_info(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an info message with structured context.
    
    Args:
        logger: Logger instance
        message: Info message
        context: Additional context information
    """
    extra = {
        'correlation_id': get_correlation_id(),
        **(context or {})
    }
    
    logger.info(message, extra=extra) 