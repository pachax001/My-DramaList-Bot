import imdb
import html
from bot.logger.logger import logger
from bot.db.user_db import get_user_imdb_template
from bot.utils.uitlities import GENRE_EMOJI


ia = imdb.Cinemagoer()

def filter_imdb(query: str) -> list:
    imdb_results = ia.search_movie(query)
    if not imdb_results:
        return []
    return imdb_results





def build_imdb_caption(user_id: int, drama_data: dict) -> str:

    """
    Generates an HTML caption from IMDB drama_data dict.
    Only uses the fields present in drama_data.
    """
    #logger.debug(f"building caption for user {user_id}")
    #logger.info(f"drama_data: {drama_data}")
    # helper to safely grab a field or fallback
    def get(key, default="N/A"):
        return drama_data.get(key, default)

    title            = get("title")
    localized_title  = get("localized_title")
    year             = get("year")
    kind             = get("kind")
    rating           = get("rating")
    votes            = get("votes")
    raw_genres       = get("genres")
    runtime          = get("runtime")
    cast             = get("cast")
    director         = get("director")
    writer           = get("writer")
    producer         = get("producer")
    composer         = get("composer")
    cinematographer  = get("cinematographer")
    music_team       = get("music_team")
    distributors     = get("distributors")
    countries        = get("countries")
    certificates     = get("certificates")
    languages        = get("languages")
    box_office       = get("box_office")
    seasons          = get("seasons")
    plot             = html.escape(get("plot"))
    poster_url       = get("poster")
    imdb_url         = get("url")
    genres_list = [g.strip() for g in raw_genres.split(",") if g.strip()]
    emoji_genres = [
        f"{GENRE_EMOJI.get(g, '')} {g}"
        for g in genres_list
    ]
    genres_with_emoji = ", ".join(emoji_genres)

    placeholders = {
        "title": title,
        "localized_title": localized_title,
        "kind": kind,
        "year": year,
        "rating": rating,
        "votes": votes,
        "runtime": runtime,
        "cast": cast,
        "director": director,
        "writer": writer,
        "producer": producer,
        "composer": composer,
        "cinematographer": cinematographer,
        "music_team": music_team,
        "distributors": distributors,
        "countries": countries,
        "certificates": certificates,
        "languages": languages,
        "box_office": box_office,
        "seasons": seasons,
        "plot": plot,
        "imdb_url": imdb_url,
        "genres": genres_with_emoji,

    }

    user_template = get_user_imdb_template(user_id)
    #logger.info("User template: %s", user_template)

    if user_template:
        try:
            valid_placeholders = {key: placeholders[key] for key in placeholders if f"{{{key}}}" in user_template}
            caption = user_template.format(**valid_placeholders)
        except Exception as e:
            caption = f"Error in template formatting: {e}"
        return caption

    else:
        caption = (
            f"<b>{placeholders['title']}</b>\n"
            f"<i>{placeholders['localized_title']}</i>\n"
    
            f"<b>Year:</b> {placeholders['year']}\n"
            f"<b>Type:</b> {placeholders['kind']}\n"
            f"<b>Rating:</b> {placeholders['rating']} ⭐️ ({placeholders['votes']} votes)\n"
            f"<b>Genres:</b> {placeholders['genres']}\n"
            f"<b>Runtime:</b> {placeholders['runtime']}\n"
            #f"<b>Cast:</b> {cast}\n\n"
    
           # f"<b>Director:</b> {director}\n"
            #f"<b>Writer:</b> {writer}\n"
            #f"<b>Producer:</b> {producer}\n"
           # f"<b>Composer:</b> {composer}\n"
            #f"<b>Cinematographer:</b> {cinematographer}\n"
           # f"<b>Music Dept.:</b> {music_team}\n"
           # f"<b>Distributors:</b> {distributors}\n\n"
    
            f"<b>Country:</b> {placeholders['countries']}\n"
           # f"<b>Certificates:</b> {certificates}\n"
            f"<b>Languages:</b> {placeholders['languages']}\n"
            f"<b>Box Office:</b> {placeholders['box_office']}\n"
            f"<b>Seasons:</b> {placeholders['seasons']}\n\n"
    
            f"<b>Plot:</b> {placeholders['plot']}\n\n"
    
            #f"<a href='{poster_url}'>🖼️ Poster</a> "
            f"<a href='{placeholders['imdb_url']}'>More on IMDb</a>"
        )

        return caption

