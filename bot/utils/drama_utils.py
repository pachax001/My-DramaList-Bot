# drama_utils.py

import requests
import html
from config import API_URL, DETAILS_API_URL
from bot.db.user_db import get_user_template
# Genre -> Emoji Mappings
GENRE_EMOJI = {
    "Action": "🚀",
    "Adult": "🔞",
    "Adventure": "🌋",
    "Animation": "🎠",
    "Biography": "📜",
    "Comedy": "🪗",
    "Crime": "🔪",
    "Documentary": "🎞",
    "Drama": "🎭",
    "Family": "👨‍👩‍👧‍👦",
    "Fantasy": "🫧",
    "Film Noir": "🎯",
    "Game Show": "🎮",
    "History": "🏛",
    "Horror": "🧟",
    "Musical": "🎻",
    "Music": "🎸",
    "Mystery": "🧳",
    "News": "📰",
    "Reality-TV": "🖥",
    "Romance": "🥰",
    "Sci-Fi": "🌠",
    "Short": "📝",
    "Sport": "⛳",
    "Talk-Show": "👨‍🍳",
    "Thriller": "🗡",
    "War": "⚔",
    "Western": "🪩",
}


def filter_dramas(query: str) -> list:
    """
    Searches for dramas with the external API using API_URL.
    Returns a list of drama dicts (title, year, slug, thumb, etc.).
    """
    response = requests.get(API_URL.format(query))
    if response.status_code == 200:
        data = response.json()
        return data.get("results", {}).get("dramas", [])
    return []


def get_drama_details(slug: str) -> dict:
    """
    Fetches detailed info for a specific drama from DETAILS_API_URL.
    Returns a dict or empty if fails.
    """
    response = requests.get(DETAILS_API_URL.format(slug))
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {})
    return {}




def build_drama_caption(user_id: int, drama_data: dict, slug: str) -> str:
    """
    Generates an HTML caption from drama details.
    Supports user-specific templates if set, otherwise defaults to standard formatting.
    Ignores unknown placeholders without throwing an error.
    """

    # Extract necessary data with defaults
    def get_field(data, field, default="N/A"):
        return data.get(field, default)

    details = get_field(drama_data, "details", {})
    others = get_field(drama_data, "others", {})

    def get_nested_field(data, field, default="N/A"):
        value = get_field(data, field, default)
        return value[0] if isinstance(value, list) and value else default

    # Build necessary fields
    title = get_field(drama_data, "title")
    complete_title = get_field(drama_data, "complete_title")
    drama_link = get_field(drama_data, "link", f"https://mydramalist.com/{slug}")

    native_title = get_nested_field(others, "native_title")
    also_known_as = ", ".join(get_field(others, "also_known_as", [])) or "N/A"
    storyline = html.escape(get_field(drama_data, "synopsis"))[:100] + "..."

    # Process genres with emojis
    genres_list = get_field(others, "genres", [])
    genres_str = ", ".join(f"{GENRE_EMOJI.get(g, '')} #{g}".replace("-", "_") for g in genres_list)

    # Process tags and clean up unnecessary suffix
    tags_list = get_field(others, "tags", [])
    if tags_list and tags_list[-1].endswith("(Vote or add tags)"):
        tags_list[-1] = tags_list[-1].replace("(Vote or add tags)", "").strip()
    tags_str = ", ".join(tags_list)

    # Define available placeholders for user-defined templates
    placeholders = {
        "title": title,
        "complete_title": complete_title,
        "link": drama_link,
        "rating": str(get_field(drama_data, "rating")),
        "synopsis": storyline,
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

    # Fetch user's custom template from the database
    user_template = get_user_template(user_id)

    # If user template exists, apply it with error handling for invalid placeholders
    if user_template:
        try:
            valid_placeholders = {key: placeholders[key] for key in placeholders if f"{{{key}}}" in user_template}
            caption = user_template.format(**valid_placeholders)
        except Exception as e:
            caption = f"Error in template formatting: {e}"
    else:
        # Default caption template
        caption = (
            f"<b>{placeholders['title']}</b>\n"
            f"<i>{placeholders['complete_title']}</i>\n"
            f"<b>Native Title:</b> {placeholders['native_title']}\n"
            f"<b>Also Known As:</b> {placeholders['also_known_as']}\n"
            f"<b>Rating ⭐️:</b> {placeholders['rating']}\n"
            f"<b>Country:</b> {placeholders['country']}\n"
            f"<b>Episodes:</b> {placeholders['episodes']}\n"
            f"<b>Aired Date:</b> {placeholders['aired']}\n"
            f"<b>Aired On:</b> {placeholders['aired_on']}\n"
            f"<b>Original Network:</b> {placeholders['original_network']}\n"
            f"<b>Duration:</b> {placeholders['duration']}\n"
            f"<b>Content Rating:</b> {placeholders['content_rating']}\n"
            f"<b>Genres:</b> {placeholders['genres']}\n"
            f"<b>Tags:</b> {placeholders['tags']}\n"
            f"<b>Storyline:</b> {placeholders['synopsis']}... \n"
            f"<a href='{placeholders['link']}'>See more...</a>"
        )

    return caption
