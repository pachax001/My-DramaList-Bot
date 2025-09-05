"""Async HTTP client with connection pooling and retry logic."""

import asyncio
import json
import random
from typing import Any, Dict, Optional
import aiohttp
from aiohttp import ClientSession, ClientTimeout
from infra.config import settings
from infra.logging import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """Async HTTP client with connection pooling, timeouts, and retry logic."""
    
    def __init__(self) -> None:
        self._session: Optional[ClientSession] = None
        self._connector = aiohttp.TCPConnector(
            limit=settings.max_connections,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
    
    async def __aenter__(self) -> "HTTPClient":
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    async def start(self) -> None:
        """Initialize the HTTP session."""
        if self._session is None:
            timeout = ClientTimeout(total=settings.http_timeout)
            self._session = ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers={'User-Agent': 'MyDramaList-Bot/2.0'}
            )
            logger.info("HTTP client started with connection pooling")
    
    async def close(self) -> None:
        """Close the HTTP session and connector."""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("HTTP client closed")
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        timeout: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Make GET request with retry logic and timeouts."""
        if not self._session:
            await self.start()
            
        request_timeout = timeout or settings.http_timeout
        
        for attempt in range(max_retries + 1):
            try:
                timeout_obj = ClientTimeout(total=request_timeout)
                async with self._session.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=timeout_obj
                ) as response:
                    response.raise_for_status()
                    
                    # Handle different content types
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        data = await response.json()
                    else:
                        # Fallback for non-JSON responses
                        text = await response.text()
                        try:
                            import json
                            data = json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning(f"Non-JSON response from {url}: {content_type}")
                            return None
                    
                    logger.debug(f"GET {url} -> {response.status}")
                    return data
                    
            except asyncio.TimeoutError:
                if attempt == max_retries:
                    logger.error(f"GET {url} timeout after {max_retries + 1} attempts ({request_timeout}s each)")
                    return None
                logger.warning(f"GET {url} timeout (attempt {attempt + 1}), retrying...")
                
            except aiohttp.ClientError as e:
                if attempt == max_retries:
                    logger.error(f"GET {url} failed after {max_retries + 1} attempts: {e}")
                    return None
                
                # Don't retry on client errors (4xx), only server errors (5xx) and network issues
                if hasattr(e, 'status') and 400 <= e.status < 500:
                    logger.error(f"GET {url} client error {e.status}, not retrying")
                    return None
            
            # Exponential backoff with jitter for retries
            if attempt < max_retries:
                delay = min(60, (2 ** attempt) + random.uniform(0, 1))  # Cap at 60s
                logger.warning(f"GET {url} failed (attempt {attempt + 1}), retrying in {delay:.1f}s")
                await asyncio.sleep(delay)
        
        return None


# Global HTTP client instance
http_client = HTTPClient()