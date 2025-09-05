"""Template processing service (pure domain logic)."""

from typing import Dict, Any, Optional
import html


class TemplateService:
    """Handles template processing and caption generation."""
    
    GENRE_EMOJI = {
        "Action": "🥊", "Adventure": "🗺️", "Comedy": "😂", "Crime": "🕵️",
        "Drama": "🎭", "Fantasy": "🧙", "Historical": "🏛️", "Horror": "👻",
        "Romance": "💕", "Sci-Fi": "🚀", "Thriller": "😱", "Mystery": "🔍",
        "Musical": "🎵", "Animation": "🎨", "Documentary": "📹", "Family": "👨‍👩‍👧‍👦",
        "War": "⚔️", "Western": "🤠", "Sports": "🏆", "Biography": "📚",
        "Music": "🎶", "News": "📰", "Reality-TV": "📺", "Talk-Show": "🎤"
    }
    
    def build_mdl_caption(
        self,
        drama_data: Dict[str, Any], 
        slug: str,
        user_template: Optional[str] = None
    ) -> str:
        """Build MyDramaList caption with template support."""
        
        def get_field(data: Dict, field: str, default: str = "N/A") -> str:
            return str(data.get(field, default))
        
        def get_nested_field(data: Dict, field: str, default: str = "N/A") -> str:
            value = get_field(data, field, default)
            if isinstance(value, list) and value:
                return value[0]
            return default if value == "N/A" else value
        
        # Handle both old and new data structure
        if "data" in drama_data:
            # New API structure
            data = drama_data["data"]
            details = data.get("details", {})
            others = data.get("others", {})
            main_data = data
        else:
            # Old API structure (fallback)
            details = drama_data.get("details", {})
            others = drama_data.get("others", {})
            main_data = drama_data
        
        title = get_field(main_data, "title")
        complete_title = get_field(main_data, "complete_title") 
        drama_link = get_field(main_data, "link", f"https://mydramalist.com/{slug}")
        
        # Handle native title (can be string or list)
        native_title_raw = others.get("native_title", [])
        if isinstance(native_title_raw, list) and native_title_raw:
            native_title = native_title_raw[0]
        elif isinstance(native_title_raw, str):
            native_title = native_title_raw
        else:
            native_title = "N/A"
        
        # Handle also known as (list to string)
        also_known_as_list = others.get("also_known_as", [])
        also_known_as = ", ".join(also_known_as_list) if also_known_as_list else "N/A"
        
        # Handle synopsis
        synopsis_raw = get_field(main_data, "synopsis")
        if synopsis_raw and synopsis_raw != "N/A":
            synopsis = html.escape(synopsis_raw)
            if len(synopsis) > 300:
                synopsis = synopsis[:300] + "..."
        else:
            synopsis = "N/A"
        
        # Process genres with emojis
        genres_list = others.get("genres", [])
        if genres_list:
            genres_str = ", ".join(
                f"{self.GENRE_EMOJI.get(g, '')} #{g}".replace("-", "_") 
                for g in genres_list
            ).strip()
        else:
            genres_str = "N/A"
        
        # Process tags
        tags_list = others.get("tags", [])
        if tags_list:
            # Clean up tags - remove vote prompts
            cleaned_tags = []
            for tag in tags_list:
                if isinstance(tag, str):
                    tag = tag.replace("(Vote tags)", "").replace("(Vote or add tags)", "").strip()
                    if tag:  # Only add non-empty tags
                        cleaned_tags.append(tag)
            tags_str = ", ".join(cleaned_tags) if cleaned_tags else "N/A"
        else:
            tags_str = "N/A"
        
        # Build placeholders
        placeholders = {
            "title": title,
            "complete_title": complete_title,
            "link": drama_link,
            "rating": str(get_field(main_data, "rating")),
            "synopsis": synopsis,
            "country": get_field(details, "country"),
            "type": get_field(details, "type"),
            "episodes": get_field(details, "episodes"),
            "aired": get_field(details, "aired"),
            "aired_on": get_field(details, "aired_on"),
            "original_network": get_field(details, "original_network"),
            "duration": get_field(details, "duration"),
            "content_rating": get_field(details, "content_rating"),
            "score": get_field(details, "score"),
            "ranked": get_field(details, "ranked"),
            "popularity": get_field(details, "popularity"),
            "watchers": get_field(details, "watchers"),
            "favorites": get_field(details, "favorites"),
            "genres": genres_str,
            "tags": tags_str,
            "native_title": native_title,
            "also_known_as": also_known_as,
            "year": get_field(main_data, "year", "N/A"),
            "release_date": get_field(details, "release_date", get_field(details, "aired", "N/A")),
            "poster": get_field(main_data, "poster", ""),
        }
        
        # Apply user template or default
        if user_template:
            return self._apply_template(user_template, placeholders)
        
        return self._build_default_mdl_caption(placeholders)
    
    def build_imdb_caption(
        self,
        imdb_data: Dict[str, Any],
        user_template: Optional[str] = None
    ) -> str:
        """Build IMDB caption with template support."""
        
        def get(key: str, default: str = "N/A") -> str:
            return str(imdb_data.get(key, default))
        
        # Process genres with emojis
        raw_genres = get("genres")
        if raw_genres != "N/A":
            genres_list = [g.strip() for g in raw_genres.split(",") if g.strip()]
            emoji_genres = [f"{self.GENRE_EMOJI.get(g, '')} {g}" for g in genres_list]
            genres_with_emoji = ", ".join(emoji_genres)
        else:
            genres_with_emoji = "N/A"
        
        placeholders = {
            # Basic Information
            "title": get("title"),
            "kind": get("kind"),
            "year": get("year"),
            "rating": get("rating"),
            "votes": get("votes"),
            "runtime": get("runtime"),
            "countries": get("countries"),
            "languages": get("languages"),
            "mpaa": get("mpaa"),
            "plot": get("plot"),
            "imdb_url": get("imdb_url"),
            "imdb_id": get("imdb_id"),
            "poster": get("poster"),
            "genres": genres_with_emoji,
            
            # People (detailed with characters for cast)
            "cast": get("cast"),
            "cast_simple": get("cast_simple"),
            "directors": get("directors"),
            "writers": get("writers"),
            "producers": get("producers"),
            "composers": get("composers"),
            "cinematographers": get("cinematographers"),
            "editors": get("editors"),
            "production_designers": get("production_designers"),
            "costume_designers": get("costume_designers"),
            
            # Series/Episode Information
            "is_series": get("is_series"),
            "is_episode": get("is_episode"),
            "series_info": get("series_info"),
            "episode_info": get("episode_info"),
            
            # Release Information
            "release_dates": get("release_dates"),
            "premiere_date": get("premiere_date"),
            "original_air_date": get("original_air_date"),
            
            # Technical Details
            "aspect_ratios": get("aspect_ratios"),
            "sound_mix": get("sound_mix"),
            "color_info": get("color_info"),
            
            # Box Office Information
            "budget": get("budget"),
            "gross": get("gross"),
            "box_office": get("box_office"),
            "opening_weekend_usa": get("opening_weekend_usa"),
            
            # Content Ratings
            "certificates": get("certificates"),
        }
        
        # Apply user template or default
        if user_template:
            return self._apply_template(user_template, placeholders)
        
        return self._build_default_imdb_caption(placeholders)
    
    def _apply_template(self, template: str, placeholders: Dict[str, str]) -> str:
        """Apply user template with error handling."""
        try:
            valid_placeholders = {
                key: placeholders[key] 
                for key in placeholders 
                if f"{{{key}}}" in template
            }
            return template.format(**valid_placeholders)
        except Exception as e:
            return f"Template error: {e}"
    
    def _build_default_mdl_caption(self, p: Dict[str, str]) -> str:
        """Build default MyDramaList caption with dynamic formatting for movies vs dramas."""
        content_type = p.get('type', 'Drama').lower()
        
        # Start with title
        caption_parts = [f"<b>{p['title']}</b>"]
        
        # Add native title if available
        if p['native_title'] and p['native_title'] != "N/A":
            caption_parts.append(f"<b>Native Title:</b> {p['native_title']}")
        
        # Add Also Known As if available and not too long
        if p['also_known_as'] and p['also_known_as'] != "N/A":
            also_known = p['also_known_as']
            if len(also_known) > 150:  # Truncate if too long
                also_known = also_known[:150] + "..."
            caption_parts.append(f"<b>Also Known As:</b> {also_known}")
        
        # Rating with star emoji
        if p['rating'] and p['rating'] != "N/A":
            caption_parts.append(f"<b>Rating ⭐️:</b> {p['rating']}")
        
        # Country
        if p['country'] and p['country'] != "N/A":
            caption_parts.append(f"<b>Country:</b> {p['country']}")
        
        # Dynamic content based on type
        if content_type == 'movie':
            # Movie-specific fields
            if p.get('release_date') and p['release_date'] != "N/A":
                caption_parts.append(f"<b>Release Date:</b> {p['release_date']}")
            elif p['aired'] and p['aired'] != "N/A":
                caption_parts.append(f"<b>Release Date:</b> {p['aired']}")
        else:
            # Drama/Series-specific fields
            if p['episodes'] and p['episodes'] != "N/A":
                caption_parts.append(f"<b>Episodes:</b> {p['episodes']}")
            
            if p['aired'] and p['aired'] != "N/A":
                caption_parts.append(f"<b>Aired Date:</b> {p['aired']}")
            
            if p['aired_on'] and p['aired_on'] != "N/A":
                caption_parts.append(f"<b>Aired On:</b> {p['aired_on']}")
            
            if p['original_network'] and p['original_network'] != "N/A":
                caption_parts.append(f"<b>Original Network:</b> {p['original_network']}")
        
        # Duration (common for both)
        if p['duration'] and p['duration'] != "N/A":
            caption_parts.append(f"<b>Duration:</b> {p['duration']}")
        
        # Content rating (common for both)
        if p['content_rating'] and p['content_rating'] != "N/A" and p['content_rating'] != "Not Yet Rated":
            caption_parts.append(f"<b>Content Rating:</b> {p['content_rating']}")
        
        # Genres with emojis (common for both)
        if p['genres'] and p['genres'] != "N/A":
            caption_parts.append(f"<b>Genres:</b> {p['genres']}")
        
        # Tags (limit for readability)
        if p['tags'] and p['tags'] != "N/A" and len(p['tags'].strip()) > 0:
            tags_list = [tag.strip() for tag in p['tags'].split(", ") if tag.strip()]
            # Limit to 8 tags to avoid message being too long
            display_tags = tags_list[:8]
            tags_text = ", ".join(display_tags)
            if len(tags_list) > 8:
                tags_text += " (Vote tags)"
            caption_parts.append(f"<b>Tags:</b> {tags_text}")
        
        # Synopsis/Storyline (common for both)
        if p['synopsis'] and p['synopsis'] != "N/A":
            synopsis = p['synopsis'].strip()
            # Dynamic truncation based on content type
            max_length = 250 if content_type == 'movie' else 300
            if len(synopsis) > max_length:
                synopsis = synopsis[:max_length] + "..."
            caption_parts.append(f"<b>Storyline:</b> {synopsis}")
        caption_parts.append(f"<a href='{p['link']}'>See more...</a>")
        
        return "\n".join(caption_parts)
    
    def _build_default_imdb_caption(self, p: Dict[str, str]) -> str:
        """Build default IMDB caption similar to MyDramaList format."""
        content_type = p.get('kind', 'movie').lower()
        
        # Start with title
        caption_parts = [f"<b>{p['title']}</b>"]
        
        # Year, Type, and Episode info
        info_parts = []
        if p['year'] != "N/A":
            info_parts.append(f"<b>Year:</b> {p['year']}")
        if p['kind'] != "N/A":
            info_parts.append(f"<b>Type:</b> {p['kind']}")
        if p['episode_info'] != "N/A" and p['episode_info'].strip():
            info_parts.append(f"<b>Episode:</b> {p['episode_info']}")
        
        if info_parts:
            caption_parts.append(" | ".join(info_parts))
        
        # Rating with votes and star emoji
        if p['rating'] != "N/A":
            rating_text = f"<b>Rating ⭐️:</b> {p['rating']}"
            if p['votes'] != "N/A":
                rating_text += f" ({p['votes']} votes)"
            caption_parts.append(rating_text)
        
        # Countries
        if p['countries'] != "N/A":
            caption_parts.append(f"<b>Countries:</b> {p['countries']}")
        
        # Runtime and Series info
        runtime_parts = []
        if p['runtime'] != "N/A":
            runtime_parts.append(f"<b>Runtime:</b> {p['runtime']}")
        if p['series_info'] != "N/A" and p['series_info'].strip():
            runtime_parts.append(f"<b>Series:</b> {p['series_info']}")
        
        if runtime_parts:
            caption_parts.append(" | ".join(runtime_parts))
        
        # Release information
        if content_type in ['tvseries', 'tvminiseries']:
            # For TV series, show original air date
            if p['original_air_date'] != "N/A":
                caption_parts.append(f"<b>Aired:</b> {p['original_air_date']}")
        else:
            # For movies, show premiere or release date
            if p['premiere_date'] != "N/A":
                caption_parts.append(f"<b>Premiere:</b> {p['premiere_date']}")
            elif p['release_dates'] != "N/A":
                caption_parts.append(f"<b>Released:</b> {p['release_dates']}")
        
        # Languages
        if p['languages'] != "N/A":
            caption_parts.append(f"<b>Languages:</b> {p['languages']}")
        
        # MPAA Rating
        if p['mpaa'] != "N/A":
            caption_parts.append(f"<b>Rated:</b> {p['mpaa']}")
        
        # Genres with emojis
        if p['genres'] != "N/A":
            caption_parts.append(f"<b>Genres:</b> {p['genres']}")
        
        # Directors
        if p['directors'] != "N/A":
            caption_parts.append(f"<b>Directors:</b> {p['directors']}")
        
        # Writers (if different from directors)
        if p['writers'] != "N/A" and p['writers'] != p['directors']:
            caption_parts.append(f"<b>Writers:</b> {p['writers']}")
        
        # Cast with character names (truncate if too long)
        if p['cast'] != "N/A":
            cast_text = p['cast']
            if len(cast_text) > 200:  # Truncate if too long
                cast_text = cast_text[:200] + "..."
            caption_parts.append(f"<b>Cast:</b> {cast_text}")
        
        # Box office (for movies)
        if content_type == 'movie' and p['box_office'] != "N/A":
            caption_parts.append(f"<b>Box Office:</b> {p['box_office']}")
        
        # Plot/Synopsis
        if p['plot'] != "N/A":
            plot = p['plot'].strip()
            # Dynamic truncation based on content type
            max_length = 300 if content_type in ['tvseries', 'tvminiseries'] else 250
            if len(plot) > max_length:
                plot = plot[:max_length] + "..."
            caption_parts.append(f"<b>Plot:</b> {plot}")
        
        # IMDb link
        caption_parts.append(f"\n<a href='{p['imdb_url']}'>More on IMDb</a>")
        
        return "\n".join(caption_parts)


# Global template service instance
template_service = TemplateService()