"""MyDramaList adapter with async HTTP and caching."""

from typing import Dict, List, Optional, Any
import html
from infra.http import http_client
from infra.config import settings
from infra.cache import cache_client
from infra.logging import get_logger, log_performance
from infra.ratelimit import api_limiter
import time

logger = get_logger(__name__)


class MyDramaListAdapter:
    """Async MyDramaList client with caching."""
    
    def __init__(self) -> None:
        pass
    
    async def search_dramas(self, query: str) -> List[Dict[str, Any]]:
        """Search dramas using MyDramaList API with rate limiting."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"search:{query}"
            cached = await cache_client.get("mdl_search", cache_key)
            if cached:
                log_performance("mdl_search", time.time() - start_time)
                return cached
            
            # Apply rate limiting for API protection
            if not await api_limiter.is_allowed("mydramalist", limit=30, window=60):
                logger.warning("MyDramaList API rate limit exceeded")
                return []
            
            # Make async HTTP request
            url = settings.mydramalist_api_url.format(query)
            logger.info(f"Searching MyDramaList for: {query}")
            
            data = await http_client.get(url)
            if not data:
                return []
            
            dramas = data.get("results", {}).get("dramas", [])
            logger.info(f"Found {len(dramas)} dramas for query: {query}")
            
            # Cache results for 1 hour
            await cache_client.set("mdl_search", cache_key, dramas, ttl=3600)
            
            log_performance("mdl_search", time.time() - start_time)
            return dramas
            
        except Exception as e:
            logger.error(f"MyDramaList search failed for '{query}': {e}")
            return []
    
    async def get_drama_details(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get detailed drama information by slug with rate limiting."""
        start_time = time.time()
        
        try:
            # Check cache first  
            cache_key = f"details:{slug}"
            cached = await cache_client.get("mdl_details", cache_key)
            if cached:
                log_performance("mdl_details", time.time() - start_time)
                return cached
            
            # Apply rate limiting for API protection
            if not await api_limiter.is_allowed("mydramalist_details", limit=20, window=60):
                logger.warning("MyDramaList details API rate limit exceeded")
                return None
            
            # Make async HTTP request
            url = settings.mydramalist_details_url.format(slug)
            logger.info(f"Fetching MyDramaList details for: {slug}")
            
            data = await http_client.get(url)
            if not data:
                return None
            
            details = data.get("data", {})
            
            # Cache for 24 hours (drama details don't change often)
            await cache_client.set("mdl_details", cache_key, details, ttl=86400)
            
            log_performance("mdl_details", time.time() - start_time)
            return details
            
        except Exception as e:
            logger.error(f"MyDramaList details failed for '{slug}': {e}")
            return None


# Global MyDramaList adapter instance
mydramalist_adapter = MyDramaListAdapter()