"""Performance monitoring middleware."""

import time
import asyncio
from functools import wraps
from typing import Callable, Any
from infra.logging import get_logger, log_performance, set_correlation_id
import uuid

logger = get_logger(__name__)


def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable) -> Callable:
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            # Set correlation ID for request tracing
            set_correlation_id(str(uuid.uuid4()))
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Extract user_id if available
                user_id = None
                if args and hasattr(args[1], 'from_user'):  # Pyrogram message
                    user_id = args[1].from_user.id
                
                log_performance(name, duration, user_id=user_id)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{name} failed after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


class HealthChecker:
    """Health check utilities for monitoring."""
    
    @staticmethod
    async def check_services() -> dict:
        """Check health of all services."""
        from infra.db import mongo_client
        from infra.cache import cache_client
        from infra.http import http_client
        
        results = {}
        
        # Check MongoDB
        try:
            healthy = await mongo_client.health_check()
            results['mongodb'] = 'healthy' if healthy else 'unhealthy'
        except Exception as e:
            results['mongodb'] = f'error: {e}'
        
        # Check Redis
        try:
            if cache_client._redis:
                await cache_client._redis.ping()
                results['redis'] = 'healthy'
            else:
                results['redis'] = 'disabled'
        except Exception as e:
            results['redis'] = f'error: {e}'
        
        # Check HTTP client
        try:
            if http_client._session:
                results['http'] = 'healthy'
            else:
                results['http'] = 'not_initialized'
        except Exception as e:
            results['http'] = f'error: {e}'
        
        return results