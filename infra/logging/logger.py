"""Structured logging with correlation IDs."""

import logging
import json
import sys
from typing import Any, Dict, Optional
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter with correlation ID support."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add correlation ID if available
        corr_id = correlation_id.get()
        if corr_id:
            log_data['correlation_id'] = corr_id
            
        # Add user_id if available
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger


def set_correlation_id(cid: str) -> None:
    """Set correlation ID for current context."""
    correlation_id.set(cid)


def log_performance(func_name: str, duration: float, **kwargs) -> None:
    """Log performance metrics."""
    logger = get_logger('performance')
    extra = {'user_id': kwargs.get('user_id')} if 'user_id' in kwargs else {}
    logger.info(f"{func_name} completed in {duration:.3f}s", extra=extra)