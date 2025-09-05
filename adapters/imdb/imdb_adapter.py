"""IMDB adapter using imdbinfo (async replacement for cinemagoer)."""

from typing import Dict, List, Optional, Any
import html
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from infra.logging import get_logger, log_performance
from infra.cache import cache_client
import time

try:
    from imdbinfo import search_title, get_movie
    from imdbinfo.locale import set_locale
    # Set default locale to English
    set_locale("en")
except ImportError as e:
    logger = get_logger(__name__)
    logger.error(f"imdbinfo library not available: {e}")
    search_title = None
    get_movie = None

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
            if not search_title:
                logger.error("imdbinfo library not available")
                return []
            
            # Search for titles using imdbinfo
            results = search_title(query)
            
            if not results or not hasattr(results, 'titles'):
                logger.info(f"No IMDB results found for query: {query}")
                return []
            
            # Transform results to our format
            movies = []
            for movie in results.titles[:20]:  # Limit to first 20 results
                try:
                    # Clean IMDB ID (remove 'tt' prefix if present)
                    imdb_id = movie.imdb_id
                    if imdb_id.startswith('tt'):
                        imdb_id = imdb_id[2:]
                    
                    movies.append({
                        'id': imdb_id,
                        'title': movie.title or 'Unknown Title',
                        'year': str(movie.year) if movie.year else None,
                        'kind': movie.kind or 'movie'
                    })
                except AttributeError as e:
                    logger.warning(f"Error processing movie result: {e}")
                    continue
            
            logger.info(f"Found {len(movies)} IMDB results for query: {query}")
            return movies
            
        except Exception as e:
            logger.error(f"IMDB search error for '{query}': {e}")
            return []
    
    def _sync_get_movie(self, imdb_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous IMDB movie details (runs in thread pool)."""
        try:
            if not get_movie:
                logger.error("imdbinfo library not available")
                return None
            
            # Ensure IMDB ID doesn't have 'tt' prefix for imdbinfo
            clean_id = imdb_id
            if clean_id.startswith('tt'):
                clean_id = clean_id[2:]
            
            # Get movie details using imdbinfo
            movie = get_movie(clean_id)
            
            if not movie:
                logger.warning(f"No IMDB movie found for ID: {imdb_id}")
                return None
            
            # Helper function to safely extract list data
            def extract_names(category_list, limit=10):
                """Extract names from category list with limit."""
                if not category_list:
                    return []
                return [person.name for person in category_list[:limit] if hasattr(person, 'name')]
            
            def extract_cast_with_characters(cast_list, limit=15):
                """Extract cast with character names."""
                if not cast_list:
                    return []
                cast_info = []
                for cast_member in cast_list[:limit]:
                    if hasattr(cast_member, 'name'):
                        name = cast_member.name
                        if hasattr(cast_member, 'characters') and cast_member.characters:
                            characters = ', '.join(cast_member.characters[:2])  # Limit to 2 characters
                            cast_info.append(f"{name} ({characters})")
                        else:
                            cast_info.append(name)
                return cast_info
            
            # Extract comprehensive data from categories
            categories = getattr(movie, 'categories', {})
            
            # Basic information
            movie_data = {
                'title': getattr(movie, 'title', 'Unknown Title'),
                'year': str(getattr(movie, 'year', '')) if getattr(movie, 'year', None) else None,
                'rating': str(getattr(movie, 'rating', '')) if getattr(movie, 'rating', None) else None,
                'votes': str(getattr(movie, 'votes', '')) if getattr(movie, 'votes', None) else None,
                'plot': getattr(movie, 'plot', None),
                'genres': getattr(movie, 'genres', []),
                'runtimes': getattr(movie, 'runtimes', []),
                'countries': getattr(movie, 'countries', []),
                'country_codes': getattr(movie, 'country_codes', []),
                'languages': getattr(movie, 'languages', []),
                'languages_text': getattr(movie, 'languages_text', []),
                'mpaa': getattr(movie, 'mpaa', None),
                'kind': getattr(movie, 'kind', 'movie'),
                'url': getattr(movie, 'url', None),
                'cover_url': getattr(movie, 'cover_url', None),
                'imdb_id': f"tt{clean_id}",
                
                # Series/Episode specific
                'is_series': movie.is_series() if hasattr(movie, 'is_series') else False,
                'is_episode': movie.is_episode() if hasattr(movie, 'is_episode') else False,
                'info_series': getattr(movie, 'info_series', None),
                'info_episode': getattr(movie, 'info_episode', None),
                
                # Release information
                'release_dates': getattr(movie, 'release_dates', []),
                'premiere_date': getattr(movie, 'premiere_date', None),
                'original_air_date': getattr(movie, 'original_air_date', None),
                
                # Technical details
                'aspect_ratios': getattr(movie, 'aspect_ratios', []),
                'sound_mix': getattr(movie, 'sound_mix', []),
                'color_info': getattr(movie, 'color_info', []),
                'cameras': getattr(movie, 'cameras', []),
                
                # Box office and awards
                'budget': getattr(movie, 'budget', None),
                'gross': getattr(movie, 'gross', None),
                'weekend': getattr(movie, 'weekend', None),
                'opening_weekend_usa': getattr(movie, 'opening_weekend_usa', None),
                
                # Content ratings
                'certificates': getattr(movie, 'certificates', []),
                'parents_guide': getattr(movie, 'parents_guide', {}),
                
                # People categories
                'cast': extract_cast_with_characters(categories.get('cast', []), 15),
                'cast_simple': extract_names(categories.get('cast', []), 10),
                'writers': extract_names(categories.get('writer', []), 5),
                'producers': extract_names(categories.get('producer', []), 5),
                'composers': extract_names(categories.get('composer', []), 3),
                'cinematographers': extract_names(categories.get('cinematographer', []), 3),
                'editors': extract_names(categories.get('editor', []), 3),
                'production_designers': extract_names(categories.get('production_designer', []), 2),
                'costume_designers': extract_names(categories.get('costume_designer', []), 2),
            }
            
            # Add directors separately (keeping backward compatibility)
            movie_data['directors'] = extract_names(categories.get('director', []), 5)
            
            logger.info(f"Successfully fetched IMDB details for: {movie_data['title']} ({movie_data['year']}) - {movie_data['kind']}")
            return movie_data
            
        except Exception as e:
            logger.error(f"IMDB details error for '{imdb_id}': {e}")
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
        
        # Plot handling - imdbinfo returns plot as a list or string
        plot_raw = movie.get('plot')
        if isinstance(plot_raw, list) and plot_raw:
            plot_raw = plot_raw[0] if plot_raw[0] else ""
        
        # Ensure plot is a string before processing
        if plot_raw and isinstance(plot_raw, str):
            # Clean up the plot - remove "See full summary »" and similar
            plot_raw = re.sub(r'\s*See full .*?»\s*$', '', plot_raw, flags=re.IGNORECASE)
            if len(plot_raw) > 300:
                plot_raw = plot_raw[:300] + "..."
            plot = html.escape(plot_raw) if plot_raw.strip() else "No plot available"
        else:
            plot = "No plot available"
        
        # Ensure IMDB ID has 'tt' prefix
        clean_imdb_id = imdb_id
        if not clean_imdb_id.startswith('tt'):
            clean_imdb_id = f"tt{clean_imdb_id}"
        
        # Runtime conversion - imdbinfo returns minutes as int/string
        runtime_list = movie.get('runtimes', [])
        if runtime_list:
            if isinstance(runtime_list[0], (int, float)):
                runtime = f"{runtime_list[0]} min"
            else:
                runtime = str(runtime_list[0])
        else:
            runtime = "N/A"
        
        # Series/Episode information processing
        series_info = ""
        episode_info = ""
        
        if movie.get('is_series'):
            info = movie.get('info_series')
            if info:
                series_info = f"Seasons: {getattr(info, 'display_seasons', 'N/A')}"
        
        if movie.get('is_episode'):
            info = movie.get('info_episode')
            if info:
                season = getattr(info, 'season', 'N/A')
                episode = getattr(info, 'episode', 'N/A')
                episode_info = f"S{season}E{episode}"
        
        # Box office processing
        budget = safe(movie.get('budget'))
        gross = safe(movie.get('gross'))
        box_office = "N/A"
        if budget != "N/A" or gross != "N/A":
            parts = []
            if budget != "N/A":
                parts.append(f"Budget: {budget}")
            if gross != "N/A":
                parts.append(f"Gross: {gross}")
            box_office = " | ".join(parts)
        
        return {
            # Basic information
            'title': safe(movie.get('title')),
            'kind': safe(movie.get('kind')),
            'year': safe(movie.get('year')),
            'rating': safe(movie.get('rating')),
            'votes': safe(movie.get('votes')),
            'runtime': runtime,
            'genres': list_to_str(movie.get('genres')),
            'countries': list_to_str(movie.get('countries')),
            'languages': list_to_str(movie.get('languages_text') or movie.get('languages')),
            'mpaa': safe(movie.get('mpaa')),
            'plot': plot,
            'poster': safe(movie.get('cover_url')),
            'imdb_url': movie.get('url') or f'https://www.imdb.com/title/{clean_imdb_id}/',
            'imdb_id': clean_imdb_id,
            
            # People
            'cast': list_to_str(movie.get('cast')),
            'cast_simple': list_to_str(movie.get('cast_simple')),
            'directors': list_to_str(movie.get('directors')),
            'writers': list_to_str(movie.get('writers')),
            'producers': list_to_str(movie.get('producers')),
            'composers': list_to_str(movie.get('composers')),
            'cinematographers': list_to_str(movie.get('cinematographers')),
            'editors': list_to_str(movie.get('editors')),
            'production_designers': list_to_str(movie.get('production_designers')),
            'costume_designers': list_to_str(movie.get('costume_designers')),
            
            # Series/Episode specific
            'is_series': safe(str(movie.get('is_series', False))),
            'is_episode': safe(str(movie.get('is_episode', False))),
            'series_info': series_info,
            'episode_info': episode_info,
            
            # Release information
            'release_dates': list_to_str(movie.get('release_dates')),
            'premiere_date': safe(movie.get('premiere_date')),
            'original_air_date': safe(movie.get('original_air_date')),
            
            # Technical details
            'aspect_ratios': list_to_str(movie.get('aspect_ratios')),
            'sound_mix': list_to_str(movie.get('sound_mix')),
            'color_info': list_to_str(movie.get('color_info')),
            
            # Box office
            'budget': safe(movie.get('budget')),
            'gross': safe(movie.get('gross')),
            'box_office': box_office,
            'opening_weekend_usa': safe(movie.get('opening_weekend_usa')),
            
            # Content ratings
            'certificates': list_to_str(movie.get('certificates')),
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