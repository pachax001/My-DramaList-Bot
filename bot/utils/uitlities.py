def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    else:
        return ' '.join(f'{elem}, ' for elem in k)


GENRE_EMOJI = {
    "Action": "💥",          # Explosion for high-energy scenes
    "Adult": "🔞",           # Explicit content warning
    "Adventure": "🗺️",       # World map for exploration
    "Animation": "🖌️",       # Paintbrush for art/creation
    "Biography": "📜",       # Scroll for historical accounts
    "Comedy": "😂",          # Laughing face for humor
    "Crime": "🚨",           # Police light for lawbreaking
    "Documentary": "🎥",     # Movie camera for realism
    "Drama": "🎭",           # Theater masks for emotional stories
    "Family": "👨👩👧👦",    # Family emoji
    "Fantasy": "🐉",         # Dragon for mythical worlds
    "Film Noir": "🕶️",      # Sunglasses for dark, moody style
    "Game Show": "🏆",       # Trophy for competition
    "History": "🏛️",         # Greek building for antiquity
    "Horror": "👻",          # Ghost for scares
    "Musical": "🎵",         # Musical notes for song-driven stories
    "Music": "🎸",           # Guitar for music-centric content
    "Mystery": "🕵️♂️",      # Detective for puzzles
    "News": "📰",            # Newspaper
    "Reality-TV": "📺",      # Television for unscripted shows
    "Romance": "💖",         # Heart for love stories
    "Sci-Fi": "👽",          # Alien for futuristic themes
    "Short": "⏳",           # Hourglass for brief runtime
    "Sport": "⚽",           # Soccer ball for athletics
    "Talk-Show": "🎙️",      # Microphone for interviews
    "Thriller": "😱",        # Scared emoji for suspense
    "War": "⚔️",             # Crossed swords
    "Western": "🤠",         # Cowboy hat
    # Additional Genres:
    "Disaster": "🌋",        # Volcano for catastrophe
    "Superhero": "🦸",       # Superhero emoji
    "Anime": "🗾",           # Japanese map for anime
    "Teen": "🎒",            # Backpack for teen themes
    "Children": "🧸",        # Teddy bear for kids' content
}
