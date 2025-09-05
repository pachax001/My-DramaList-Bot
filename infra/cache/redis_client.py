"""Redis caching with TTL management."""

import asyncio
import json
import hashlib
from typing import Any, Optional, Union
import aioredis
from infra.config import settings
from infra.logging import get_logger

logger = get_logger(__name__)


class CacheClient:
    """Redis client with intelligent caching and TTL management."""
    
    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None
    
    async def start(self) -> None:
        """Initialize Redis connection with connection pooling."""
        try:
            self._redis = await aioredis.from_url(
                settings.redis_url,
                encoding='utf-8',
                decode_responses=True,
                max_connections=20,  # Connection pool size
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            # Test connection with timeout
            await asyncio.wait_for(self._redis.ping(), timeout=5.0)
            logger.info("Redis cache client connected with connection pooling")
        except asyncio.TimeoutError:
            logger.warning("Redis connection timeout, caching disabled")
            self._redis = None
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            self._redis = None
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            try:
                await self._redis.close()
                logger.info("Redis cache client closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace and version."""
        # Add version prefix for cache invalidation if needed
        return f"v1:{namespace}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Generate hash for complex keys."""
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis:
            return None
            
        try:
            cache_key = self._make_key(namespace, key)
            value = await self._redis.get(cache_key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get failed for {namespace}:{key}: {e}")
        
        return None
    
    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._redis:
            return False
            
        try:
            cache_key = self._make_key(namespace, key)
            serialized = json.dumps(value)
            
            if ttl:
                await self._redis.setex(cache_key, ttl, serialized)
            else:
                await self._redis.set(cache_key, serialized)
            
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for {namespace}:{key}: {e}")
            return False
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete key from cache."""
        if not self._redis:
            return False
            
        try:
            cache_key = self._make_key(namespace, key)
            await self._redis.delete(cache_key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for {namespace}:{key}: {e}")
            return False
    
    async def cached_call(
        self,
        namespace: str,
        key: str,
        func,
        *args,
        ttl: int = 3600,
        cache_none: bool = False,  # Whether to cache None results
        **kwargs
    ) -> Any:
        """Execute function with intelligent caching."""
        # Try cache first
        cached = await self.get(namespace, key)
        if cached is not None:
            logger.debug(f"Cache hit for {namespace}:{key}")
            return cached
        
        # Execute function
        logger.debug(f"Cache miss for {namespace}:{key}, executing function")
        try:
            result = await func(*args, **kwargs)
            
            # Cache result based on policy
            if result is not None or cache_none:
                # Use adaptive TTL based on namespace
                adaptive_ttl = self._get_adaptive_ttl(namespace, ttl)
                await self.set(namespace, key, result, adaptive_ttl)
            
            return result
        except Exception as e:
            logger.error(f"Function execution failed for {namespace}:{key}: {e}")
            raise
    
    def _get_adaptive_ttl(self, namespace: str, default_ttl: int) -> int:
        """Get adaptive TTL based on namespace and content type."""
        ttl_map = {
            'imdb_search': 1800,      # 30 minutes - search results change less frequently
            'imdb_details': 86400,    # 24 hours - movie details rarely change
            'mdl_search': 3600,       # 1 hour - drama search results
            'mdl_details': 43200,     # 12 hours - drama details
            'user_templates': 7200,   # 2 hours - user preferences
        }
        return ttl_map.get(namespace, default_ttl)


# Global cache client instance  
cache_client = CacheClient()