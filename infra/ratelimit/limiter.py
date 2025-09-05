"""Rate limiting to protect external APIs and bot resources."""

import asyncio
import time
from typing import Dict, Optional
from infra.logging import get_logger
from infra.cache import cache_client

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter with Redis backing."""
    
    def __init__(self, namespace: str = "ratelimit") -> None:
        self.namespace = namespace
        self._local_buckets: Dict[str, Dict] = {}
        self._last_cleanup = time.time()
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int = 60,
        burst: Optional[int] = None
    ) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier for the rate limit bucket
            limit: Number of requests allowed per window
            window: Time window in seconds
            burst: Maximum burst requests (defaults to limit)
        
        Returns:
            True if request is allowed, False otherwise
        """
        burst = burst or limit
        cache_key = f"{self.namespace}:bucket:{key}"
        current_time = time.time()
        
        try:
            # Try Redis first for distributed rate limiting
            if cache_client._redis:
                return await self._redis_check(cache_key, limit, window, burst, current_time)
            else:
                # Fallback to local memory
                return await self._local_check(key, limit, window, burst, current_time)
                
        except Exception as e:
            logger.warning(f"Rate limiter error for {key}: {e}")
            # Fail open - allow request if rate limiter is broken
            return True
    
    async def _redis_check(
        self, 
        cache_key: str, 
        limit: int, 
        window: int, 
        burst: int, 
        current_time: float
    ) -> bool:
        """Redis-backed rate limiting."""
        # Use Redis for token bucket algorithm
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or burst
        local last_refill = tonumber(bucket[2]) or current_time
        
        -- Calculate tokens to add based on time passed
        local time_passed = current_time - last_refill
        local tokens_to_add = math.floor(time_passed * (limit / window))
        tokens = math.min(burst, tokens + tokens_to_add)
        
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
            redis.call('EXPIRE', key, window * 2)
            return 1
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
            redis.call('EXPIRE', key, window * 2)
            return 0
        end
        """
        
        try:
            result = await cache_client._redis.eval(
                lua_script,
                1,
                cache_key,
                str(limit),
                str(window), 
                str(burst),
                str(current_time)
            )
            return result == 1
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            return True  # Fail open
    
    async def _local_check(
        self,
        key: str,
        limit: int,
        window: int, 
        burst: int,
        current_time: float
    ) -> bool:
        """Local memory token bucket rate limiting with cleanup."""
        # Cleanup old buckets every 10 minutes
        if current_time - self._last_cleanup > 600:
            await self._cleanup_old_buckets(current_time)
            self._last_cleanup = current_time
        
        if key not in self._local_buckets:
            self._local_buckets[key] = {
                'tokens': burst,
                'last_refill': current_time
            }
        
        bucket = self._local_buckets[key]
        
        # Calculate tokens to add
        time_passed = current_time - bucket['last_refill']
        tokens_to_add = time_passed * (limit / window)
        bucket['tokens'] = min(burst, bucket['tokens'] + tokens_to_add)
        bucket['last_refill'] = current_time
        
        # Check if request is allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        
        return False
    
    async def get_remaining(self, key: str, limit: int, window: int = 60) -> int:
        """Get remaining requests in current window."""
        cache_key = f"{self.namespace}:bucket:{key}"
        
        try:
            if cache_client._redis:
                bucket = await cache_client._redis.hmget(cache_key, 'tokens')
                tokens = float(bucket[0]) if bucket[0] else limit
                return int(max(0, tokens))
            else:
                bucket = self._local_buckets.get(key, {'tokens': limit})
                return int(max(0, bucket['tokens']))
        except Exception:
            return limit  # Conservative estimate
    
    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        cache_key = f"{self.namespace}:bucket:{key}"
        
        try:
            if cache_client._redis:
                await cache_client._redis.delete(cache_key)
            else:
                self._local_buckets.pop(key, None)
        except Exception as e:
            logger.warning(f"Failed to reset rate limit for {key}: {e}")
    
    async def _cleanup_old_buckets(self, current_time: float) -> None:
        """Clean up old unused buckets to prevent memory leaks."""
        try:
            # Remove buckets that haven't been used for over 1 hour
            cleanup_threshold = 3600
            keys_to_remove = []
            
            for key, bucket in self._local_buckets.items():
                if current_time - bucket['last_refill'] > cleanup_threshold:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._local_buckets[key]
            
            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")
                
        except Exception as e:
            logger.warning(f"Error during bucket cleanup: {e}")


# Global rate limiter instances
api_limiter = RateLimiter("api")          # For external API calls
user_limiter = RateLimiter("user")        # For user requests
global_limiter = RateLimiter("global")    # For overall bot protection