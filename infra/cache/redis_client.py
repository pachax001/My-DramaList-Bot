"""Redis caching with TTL management."""

import asyncio
import hashlib
import json
from typing import Any, Optional

import redis.asyncio as redis

from infra.config import settings
from infra.logging import get_logger

logger = get_logger(__name__)


class CacheClient:
    """Redis client with intelligent caching and TTL management."""
    
    def __init__(self) -> None:
        self._redis: Optional[redis.Redis] = None
    
    async def start(self) -> None:
        """Initialize Redis connection with connection pooling."""
        try:
            # Create Redis connection using redis-py async
            self._redis = redis.from_url(
                settings.redis_url,
                encoding='utf-8',
                decode_responses=True,
                max_connections=20,  # Connection pool size
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection with retries and longer timeout
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await asyncio.wait_for(self._redis.ping(), timeout=10.0)
                    logger.info("Redis cache client connected with connection pooling")
                    return
                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        logger.warning(f"Redis connection timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                        await asyncio.sleep(2)
                    else:
                        logger.warning("Redis connection timeout after all retries, caching disabled")
                        self._redis = None
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Redis connection failed (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                        await asyncio.sleep(2)
                    else:
                        logger.warning(f"Redis unavailable after all retries, caching disabled: {e}")
                        self._redis = None
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            self._redis = None
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            try:
                # Close Redis connection using redis-py async
                await self._redis.aclose()
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
        """Execute function with intelligent caching and distributed locking."""
        # Try cache first
        cached = await self.get(namespace, key)
        if cached is not None:
            logger.debug(f"Cache hit for {namespace}:{key}")
            return cached
        
        # Use distributed lock to prevent race conditions
        lock_key = f"lock:{namespace}:{key}"
        lock_ttl = 30  # 30 second lock timeout
        
        if self._redis:
            try:
                # Try to acquire distributed lock
                lock_acquired = await self._redis.set(lock_key, "1", nx=True, ex=lock_ttl)
                
                if lock_acquired:
                    try:
                        # Double-check cache after acquiring lock
                        cached = await self.get(namespace, key)
                        if cached is not None:
                            logger.debug(f"Cache hit after lock for {namespace}:{key}")
                            return cached
                        
                        # Execute function
                        logger.debug(f"Cache miss for {namespace}:{key}, executing function with lock")
                        result = await func(*args, **kwargs)
                        
                        # Cache result based on policy
                        if result is not None or cache_none:
                            adaptive_ttl = self._get_adaptive_ttl(namespace, ttl)
                            await self.set(namespace, key, result, adaptive_ttl)
                        
                        return result
                    finally:
                        # Release lock
                        await self._redis.delete(lock_key)
                else:
                    # Lock not acquired, wait briefly and check cache again
                    await asyncio.sleep(0.1)
                    cached = await self.get(namespace, key)
                    if cached is not None:
                        logger.debug(f"Cache hit after waiting for {namespace}:{key}")
                        return cached
                    
                    # If still no cache hit, execute without lock (fallback)
                    logger.debug(f"Executing without lock for {namespace}:{key}")
                    result = await func(*args, **kwargs)
                    return result
                    
            except Exception as lock_error:
                logger.warning(f"Lock error for {namespace}:{key}: {lock_error}, proceeding without lock")
        
        # Fallback: execute function without distributed lock
        logger.debug(f"Cache miss for {namespace}:{key}, executing function")
        try:
            result = await func(*args, **kwargs)
            
            # Cache result based on policy
            if result is not None or cache_none:
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