import imdb
from bot.logger.logger import logger
ia = imdb.Cinemagoer()
from bot.utils.uitlities import list_to_str

def safe(value, default="Unavailable"):
    """Return value if it’s truthy, otherwise default."""
    if value is None:
        return default
    # for lists/strings that might be empty
    if hasattr(value, '__len__') and len(value) == 0:
        return default
    return value

def get_details_by_imdb_id(imdb_id):
    movie = ia.get_movie(imdb_id)
    logger.info(f"Retrieved imdb details for imdb_id: {imdb_id}")
    logger.info(f"Found {movie} imdb details")

    # Release date fallback
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = None  # will become "Unavailable" via safe()

    # Plot trimming
    plot = movie.get('plot outline')
    if plot and len(plot) > 200:
        plot = plot[:200] + "..."
    plot = safe(plot, default="No plot available")

    return {
        'title':          safe(movie.get('title')),
        'votes':          safe(movie.get('votes')),
        'aka':            safe(list_to_str(movie.get("akas"))),
        'seasons':        safe(movie.get("number of seasons")),
        'box_office':     safe(movie.get('box office')),
        'localized_title':safe(movie.get('localized title')),
        'kind':           safe(movie.get("kind")),
        'imdb_id':        safe(f"tt{movie.get('imdbID')}", default="Unavailable"),
        'cast':           safe(list_to_str(movie.get("cast"))),
        'runtime':        safe(list_to_str(movie.get("runtimes"))),
        'countries':      safe(list_to_str(movie.get("countries"))),
        'certificates':   safe(list_to_str(movie.get("certificates"))),
        'languages':      safe(list_to_str(movie.get("languages"))),
        'director':       safe(list_to_str(movie.get("director"))),
        'writer':         safe(list_to_str(movie.get("writer"))),
        'producer':       safe(list_to_str(movie.get("producer"))),
        'composer':       safe(list_to_str(movie.get("composer"))),
        'cinematographer':safe(list_to_str(movie.get("cinematographer"))),
        'music_team':     safe(list_to_str(movie.get("music department"))),
        'distributors':   safe(list_to_str(movie.get("distributors"))),
        'release_date':   safe(date),
        'year':           safe(movie.get('year')),
        'genres':         safe(list_to_str(movie.get("genres"))),
        'poster':         safe(movie.get('full-size cover url')),
        'plot':           plot,
        'rating':         safe(str(movie.get("rating"))),
        'url':            safe(f'https://www.imdb.com/title/tt{imdb_id}')
    }
