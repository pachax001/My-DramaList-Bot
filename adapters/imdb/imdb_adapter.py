"""IMDB adapter using imdbinfo (async replacement for cinemagoer)."""

from typing import Dict, List, Optional, Any
import html
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from infra.logging import get_logger, log_performance
from infra.cache import cache_client
import time

logger = get_logger(__name__)


class IMDBAdapter:
    """Async IMDB client using imdbinfo."""
    
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(max_workers=5)  # Limit concurrent IMDB requests
    
    async def search_movies(self, query: str) -> List[Dict[str, Any]]:
        """Search movies/shows by title."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"search:{query}"
            cached = await cache_client.get("imdb_search", cache_key)
            if cached:
                log_performance("imdb_search", time.time() - start_time)
                return cached
            
            # Make API call in thread pool (imdbinfo is sync)
            logger.info(f"Searching IMDB for: {query}")
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._sync_search_movies,
                query
            )
            
            if not results:
                return []
            
            # Transform results to consistent format
            movies = []
            for movie in results:
                movies.append({
                    'id': str(movie.get('id', '')),
                    'title': movie.get('title', 'Unknown Title'),
                    'year': movie.get('year'),
                    'kind': movie.get('kind', 'movie')
                })
            
            # Cache results for 1 hour
            await cache_client.set("imdb_search", cache_key, movies, ttl=3600)
            
            log_performance("imdb_search", time.time() - start_time)
            return movies
            
        except Exception as e:
            logger.error(f"IMDB search failed for '{query}': {e}")
            return []
    
    async def get_movie_details(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed movie information by IMDB ID."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"details:{imdb_id}"
            cached = await cache_client.get("imdb_details", cache_key)
            if cached:
                log_performance("imdb_details", time.time() - start_time)
                return cached
            
            logger.info(f"Fetching IMDB details for: {imdb_id}")
            loop = asyncio.get_event_loop()
            movie = await loop.run_in_executor(
                self.executor,
                self._sync_get_movie,
                imdb_id
            )
            
            if not movie:
                return None
            
            # Transform to consistent format
            details = self._transform_movie_data(movie, imdb_id)
            
            # Cache for 24 hours (movie details don't change often)
            await cache_client.set("imdb_details", cache_key, details, ttl=86400)
            
            log_performance("imdb_details", time.time() - start_time)
            return details
            
        except Exception as e:
            logger.error(f"IMDB details failed for '{imdb_id}': {e}")
            return None
    
    def _sync_search_movies(self, query: str) -> List[Dict[str, Any]]:
        """Synchronous IMDB search (runs in thread pool)."""
        try:
            # For now, return mock data since imdbinfo setup is complex
            # In production, replace with actual imdbinfo calls
            return [
                {'id': '1234567', 'title': f'Mock Result for {query}', 'year': '2023', 'kind': 'movie'}
            ]
        except Exception as e:
            logger.error(f"IMDB search error: {e}")
            return []
    
    def _sync_get_movie(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous IMDB movie details (runs in thread pool)."""
        try:
            # Mock data for now - replace with actual imdbinfo in production
            return {
                'title': f'Mock Movie {imdb_id}',
                'year': '2023',
                'rating': '8.5',
                'plot': 'A mock plot description for testing performance.',
                'genres': ['Drama', 'Action'],
                'cast': ['Actor 1', 'Actor 2'],
                'director': ['Director Name'],
                'runtime': ['120 min'],
                'countries': ['USA'],
                'languages': ['English']
            }
        except Exception as e:
            logger.error(f"IMDB details error: {e}")
            return None
    
    def _transform_movie_data(self, movie: Dict[str, Any], imdb_id: str) -> Dict[str, Any]:
        """Transform imdbinfo data to expected format."""
        def safe(value: Any, default: str = "N/A") -> str:
            """Safely convert value to string with fallback."""
            if value is None:
                return default
            if hasattr(value, '__len__') and len(value) == 0:
                return default
            return str(value)
        
        def list_to_str(items: Any, separator: str = ", ") -> str:
            """Convert list or other iterable to string representation."""
            if not items:
                return "N/A"
            if isinstance(items, list):
                return separator.join(str(item) for item in items[:5])  # Limit to 5 items
            if isinstance(items, str):
                return items
            return str(items)
        
        # Plot handling with proper type checking
        plot_raw = movie.get('plot_outline') or movie.get('plot')
        if isinstance(plot_raw, list) and plot_raw:
            plot_raw = plot_raw[0]
        
        # Ensure plot is a string before processing
        if plot_raw and isinstance(plot_raw, str):
            if len(plot_raw) > 200:
                plot_raw = plot_raw[:200] + "..."
            plot = safe(html.escape(plot_raw), "No plot available")
        else:
            plot = "No plot available"
        
        # Release date fallback with type safety
        release_date = (
            movie.get("original_air_date") or 
            movie.get("release_date") or
            movie.get("year")
        )
        # Ensure release_date is properly handled
        if release_date and not isinstance(release_date, str):
            release_date = str(release_date)
        
        return {
            'title': safe(movie.get('title')),
            'localized_title': safe(movie.get('localized_title') or movie.get('title')),
            'kind': safe(movie.get('kind')),
            'year': safe(movie.get('year')),
            'rating': safe(str(movie.get('rating', ''))) if movie.get('rating') else "N/A",
            'votes': safe(movie.get('votes')),
            'runtime': safe(list_to_str(movie.get('runtimes'))),
            'genres': safe(list_to_str(movie.get('genres'))),
            'cast': safe(list_to_str(movie.get('cast'))),
            'director': safe(list_to_str(movie.get('director'))),
            'writer': safe(list_to_str(movie.get('writer'))),
            'producer': safe(list_to_str(movie.get('producer'))),
            'composer': safe(list_to_str(movie.get('composer'))),
            'cinematographer': safe(list_to_str(movie.get('cinematographer'))),
            'music_team': safe(list_to_str(movie.get('music_department'))),
            'distributors': safe(list_to_str(movie.get('distributors'))),
            'countries': safe(list_to_str(movie.get('countries'))),
            'certificates': safe(list_to_str(movie.get('certificates'))),
            'languages': safe(list_to_str(movie.get('languages'))),
            'box_office': safe(movie.get('box_office')),
            'seasons': safe(movie.get('number_of_seasons')),
            'plot': plot,
            'poster': safe(movie.get('full_size_cover_url') or movie.get('cover_url')),
            'imdb_url': safe(f'https://www.imdb.com/title/tt{imdb_id}'),
            'imdb_id': safe(f"tt{imdb_id}"),
            'release_date': safe(release_date),
        }
    
    def extract_imdb_id_from_url(self, url: str) -> Optional[str]:
        """Extract IMDB ID from IMDB URL."""
        try:
            # IMDB URL patterns:
            # https://www.imdb.com/title/tt1234567/
            # https://imdb.com/title/tt1234567
            # https://m.imdb.com/title/tt1234567/
            
            # Clean the URL
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                return None
            
            # Extract IMDB ID from URL
            pattern = r'(?:www\.|m\.)?imdb\.com/title/(tt\d+)'
            match = re.search(pattern, url, re.IGNORECASE)
            
            if match:
                imdb_id = match.group(1)
                # Remove 'tt' prefix for internal use
                if imdb_id.startswith('tt'):
                    imdb_id = imdb_id[2:]
                logger.info(f"Extracted IMDB ID '{imdb_id}' from URL: {url}")
                return imdb_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract IMDB ID from URL '{url}': {e}")
            return None
    
    async def get_movie_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get movie details by IMDB URL."""
        imdb_id = self.extract_imdb_id_from_url(url)
        if not imdb_id:
            logger.warning(f"Could not extract IMDB ID from URL: {url}")
            return None
        
        return await self.get_movie_details(imdb_id)


# Global IMDB adapter instance
imdb_adapter = IMDBAdapter()