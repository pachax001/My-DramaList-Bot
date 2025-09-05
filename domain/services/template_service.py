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
        
        # Extract data safely
        details = drama_data.get("details", {})
        others = drama_data.get("others", {})
        
        title = get_field(drama_data, "title")
        complete_title = get_field(drama_data, "complete_title")
        drama_link = get_field(drama_data, "link", f"https://mydramalist.com/{slug}")
        
        native_title = get_nested_field(others, "native_title")
        also_known_as = ", ".join(others.get("also_known_as", [])) or "N/A"
        synopsis = html.escape(get_field(drama_data, "synopsis"))
        if len(synopsis) > 200:
            synopsis = synopsis[:200] + "..."
        
        # Process genres with emojis
        genres_list = others.get("genres", [])
        genres_str = ", ".join(
            f"{self.GENRE_EMOJI.get(g, '')} #{g}".replace("-", "_") 
            for g in genres_list
        )
        
        # Process tags
        tags_list = others.get("tags", [])
        if tags_list and tags_list[-1].endswith("(Vote or add tags)"):
            tags_list[-1] = tags_list[-1].replace("(Vote or add tags)", "").strip()
        tags_str = ", ".join(tags_list)
        
        # Build placeholders
        placeholders = {
            "title": title,
            "complete_title": complete_title,
            "link": drama_link,
            "rating": get_field(drama_data, "rating"),
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
            "title": get("title"),
            "localized_title": get("localized_title"),
            "kind": get("kind"),
            "year": get("year"),
            "rating": get("rating"),
            "votes": get("votes"),
            "runtime": get("runtime"),
            "cast": get("cast"),
            "director": get("director"),
            "writer": get("writer"),
            "producer": get("producer"),
            "composer": get("composer"),
            "cinematographer": get("cinematographer"),
            "music_team": get("music_team"),
            "distributors": get("distributors"),
            "countries": get("countries"),
            "certificates": get("certificates"),
            "languages": get("languages"),
            "box_office": get("box_office"),
            "seasons": get("seasons"),
            "plot": get("plot"),
            "imdb_url": get("imdb_url"),
            "genres": genres_with_emoji,
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
        """Build default MyDramaList caption."""
        return (
            f"<b>{p['title']}</b>\n"
            f"<i>{p['complete_title']}</i>\n"
            f"<b>Native Title:</b> {p['native_title']}\n"
            f"<b>Also Known As:</b> {p['also_known_as']}\n"
            f"<b>Rating ⭐️:</b> {p['rating']}\n"
            f"<b>Country:</b> {p['country']}\n"
            f"<b>Episodes:</b> {p['episodes']}\n"
            f"<b>Aired Date:</b> {p['aired']}\n"
            f"<b>Aired On:</b> {p['aired_on']}\n"
            f"<b>Original Network:</b> {p['original_network']}\n"
            f"<b>Duration:</b> {p['duration']}\n"
            f"<b>Content Rating:</b> {p['content_rating']}\n"
            f"<b>Genres:</b> {p['genres']}\n"
            f"<b>Tags:</b> {p['tags']}\n"
            f"<b>Storyline:</b> {p['synopsis']}...\n"
            f"<a href='{p['link']}'>See more...</a>"
        )
    
    def _build_default_imdb_caption(self, p: Dict[str, str]) -> str:
        """Build default IMDB caption."""
        return (
            f"<b>{p['title']}</b>\n"
            f"<i>{p['localized_title']}</i>\n"
            f"<b>Year:</b> {p['year']}\n"
            f"<b>Type:</b> {p['kind']}\n"
            f"<b>Rating:</b> {p['rating']} ⭐️ ({p['votes']} votes)\n"
            f"<b>Genres:</b> {p['genres']}\n"
            f"<b>Runtime:</b> {p['runtime']}\n"
            f"<b>Country:</b> {p['countries']}\n"
            f"<b>Languages:</b> {p['languages']}\n"
            f"<b>Box Office:</b> {p['box_office']}\n"
            f"<b>Seasons:</b> {p['seasons']}\n\n"
            f"<b>Plot:</b> {p['plot']}\n\n"
            f"<a href='{p['imdb_url']}'>More on IMDb</a>"
        )


# Global template service instance
template_service = TemplateService()