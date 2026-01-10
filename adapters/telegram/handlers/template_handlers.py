"""Template management handlers."""

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from infra.config import settings
from infra.logging import get_logger
from infra.db import mongo_client
from infra.cache import cache_client

logger = get_logger(__name__)


async def set_template_command(client: Client, message: Message):
    """Set MyDramaList template for user."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "<b>Usage:</b> <code>/setmdltemplate &lt;template&gt;</code> or reply to a template message\n\n"
                "<b>Example Template:</b>\n"
                "<pre>\n"
                "🎭 &lt;b&gt;{title}&lt;/b&gt;\n"
                "📍 {country} | Episodes: {episodes}\n"
                "⭐ Rating: {rating}\n"
                "🎬 Genres: {genres}\n"
                "📖 {synopsis}\n"
                "</pre>\n\n"
                "<b>Popular Placeholders:</b>\n"
                "• <code>{title}</code> - Drama title\n"
                "• <code>{rating}</code> - User rating\n"
                "• <code>{synopsis}</code> - Plot summary\n"
                "• <code>{country}</code> - Country of origin\n"
                "• <code>{episodes}</code> - Number of episodes\n"
                "• <code>{genres}</code> - Genres with emojis\n"
                "• <code>{year}</code> - Release year\n\n"
                "Use /mdlplaceholders to see all available placeholders!",
                parse_mode=ParseMode.HTML
            )
            return
        template = parts[1]
    
    try:
        # Save template to database
        await mongo_client.db.mdl_templates.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "template": template}},
            upsert=True
        )
        
        # Invalidate user template cache
        await cache_client.delete("user_templates", f"mdl_{user_id}")
        
        logger.info(f"User {user_id} set MDL template")
        await message.reply_text("✅ MyDramaList template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting MDL template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_template_command(client: Client, message: Message):
    """Get user's MyDramaList template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        # Try cache first
        template = await cache_client.get("user_templates", f"mdl_{user_id}")
        
        if template is None:
            # Cache miss, get from database
            template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
            if template_doc:
                template = template_doc.get("template", "")
                # Cache the template for 2 hours
                await cache_client.set("user_templates", f"mdl_{user_id}", template, ttl=7200)
        
        if template:
            await message.reply_text(f"📝 Your current MyDramaList template:\n\n<code>{template}</code>", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("ℹ️ You don't have a custom MyDramaList template set.")
            
    except Exception as e:
        logger.error(f"Error getting MDL template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_template_command(client: Client, message: Message):
    """Remove user's MyDramaList template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        result = await mongo_client.db.mdl_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            # Invalidate user template cache
            await cache_client.delete("user_templates", f"mdl_{user_id}")
            
            logger.info(f"User {user_id} removed MDL template")
            await message.reply_text("✅ MyDramaList template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have a MyDramaList template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing MDL template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_template_command(client: Client, message: Message):
    """Preview user's MyDramaList template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        # Try cache first
        template = await cache_client.get("user_templates", f"mdl_{user_id}")
        
        if template is None:
            # Cache miss, get from database
            template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
            if template_doc:
                template = template_doc.get("template", "")
                # Cache the template for 2 hours
                await cache_client.set("user_templates", f"mdl_{user_id}", template, ttl=7200)
        
        if not template:
            await message.reply_text("ℹ️ You don't have a custom MyDramaList template set.")
            return
        
        # Mock data for preview (comprehensive)
        mock_data = {
            "title": "Sample Drama",
            "complete_title": "Sample Drama: The Complete Title",
            "native_title": "샘플 드라마",
            "also_known_as": "Sample, Example Drama",
            "rating": "8.5",
            "synopsis": "This is a sample synopsis for preview. A compelling story about...",
            "country": "South Korea",
            "episodes": "16",
            "genres": "🎭 Romance, 😂 Comedy",
            "year": "2023",
            "type": "Drama",
            "duration": "60 min",
            "aired": "2023-01-01 to 2023-04-30",
            "aired_on": "tvN",
            "original_network": "tvN",
            "content_rating": "15+",
            "score": "8.5",
            "ranked": "#25",
            "popularity": "#15", 
            "watchers": "12,345",
            "favorites": "1,234",
            "tags": "Drama, Romance, Comedy",
            "poster": "https://example.com/poster.jpg",
            "link": "https://mydramalist.com/sample-drama",
            "release_date": "January 1, 2023"
        }
        
        try:
            preview = template.format(**mock_data)
            await message.reply_text(f"👁️ <b>Template Preview:</b>\n\n{preview}", parse_mode=ParseMode.HTML)
        except KeyError as e:
            await message.reply_text(f"❌ Template error: Unknown placeholder {e}")
        except Exception as e:
            await message.reply_text(f"❌ Template formatting error: {e}")
            
    except Exception as e:
        logger.error(f"Error previewing MDL template: {e}")
        await message.reply_text("❌ Failed to preview template.")


# IMDB Template handlers
async def set_imdb_template_command(client: Client, message: Message):
    """Set IMDB template for user."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "<b>Usage:</b> <code>/setimdbtemplate &lt;template&gt;</code> or reply to a template message\n\n"
                "<b>Example Template:</b>\n"
                "<pre>\n"
                "🎬 &lt;b&gt;{title}&lt;/b&gt; ({year})\n"
                "⭐ {rating}/10 ({votes} votes)\n"
                "🎭 Cast: {cast}\n"
                "🎬 Directors: {directors}\n"
                "📝 {plot}\n"
                "</pre>\n\n"
                "<b>Popular Placeholders:</b>\n"
                "• <code>{title}</code> - Movie/show title\n"
                "• <code>{year}</code> - Release year\n"
                "• <code>{rating}</code> - IMDB rating\n"
                "• <code>{votes}</code> - Number of votes\n"
                "• <code>{cast}</code> - Main cast with characters\n"
                "• <code>{directors}</code> - Directors\n"
                "• <code>{plot}</code> - Plot summary\n"
                "• <code>{genres}</code> - Genres with emojis\n\n"
                "Use /imdbplaceholders to see all 50+ available placeholders!",
                parse_mode=ParseMode.HTML
            )
            return
        template = parts[1]
    
    try:
        # Save template to database
        await mongo_client.db.imdb_templates.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "template": template}},
            upsert=True
        )
        
        # Invalidate user template cache
        await cache_client.delete("user_templates", f"imdb_{user_id}")
        
        logger.info(f"User {user_id} set IMDB template")
        await message.reply_text("✅ IMDB template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting IMDB template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_imdb_template_command(client: Client, message: Message):
    """Get user's IMDB template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        # Try cache first
        template = await cache_client.get("user_templates", f"imdb_{user_id}")
        
        if template is None:
            # Cache miss, get from database
            template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
            if template_doc:
                template = template_doc.get("template", "")
                # Cache the template for 2 hours
                await cache_client.set("user_templates", f"imdb_{user_id}", template, ttl=7200)
        
        if template:
            await message.reply_text(f"📝 Your current IMDB template:\n\n<code>{template}</code>", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("ℹ️ You don't have a custom IMDB template set.")
            
    except Exception as e:
        logger.error(f"Error getting IMDB template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_imdb_template_command(client: Client, message: Message):
    """Remove user's IMDB template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        result = await mongo_client.db.imdb_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            # Invalidate user template cache
            await cache_client.delete("user_templates", f"imdb_{user_id}")
            
            logger.info(f"User {user_id} removed IMDB template")
            await message.reply_text("✅ IMDB template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have an IMDB template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing IMDB template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_imdb_template_command(client: Client, message: Message):
    """Preview user's IMDB template."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    
    try:
        # Try cache first
        template = await cache_client.get("user_templates", f"imdb_{user_id}")
        
        if template is None:
            # Cache miss, get from database
            template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
            if template_doc:
                template = template_doc.get("template", "")
                # Cache the template for 2 hours
                await cache_client.set("user_templates", f"imdb_{user_id}", template, ttl=7200)
        
        if not template:
            await message.reply_text("ℹ️ You don't have a custom IMDB template set.")
            return
        
        # Mock data for preview (comprehensive)
        mock_data = {
            "title": "Sample Movie",
            "kind": "movie",
            "year": "2023",
            "rating": "8.7", 
            "votes": "125,456",
            "runtime": "142 min",
            "plot": "This is a sample plot for preview purposes. An epic tale of adventure...",
            "cast": "John Doe (Hero), Jane Smith (Heroine), Bob Wilson (Villain)",
            "cast_simple": "John Doe, Jane Smith, Bob Wilson",
            "directors": "Director Name",
            "writers": "Writer A, Writer B",
            "producers": "Producer X, Producer Y",
            "composers": "Composer Z",
            "cinematographers": "Camera Director",
            "editors": "Editor Name",
            "production_designers": "Design Lead",
            "costume_designers": "Costume Head",
            "genres": "🎭 Drama, 🎬 Action",
            "countries": "United States",
            "languages": "English, Spanish",
            "mpaa": "PG-13",
            "certificates": "US:PG-13, UK:12A",
            "imdb_url": "https://imdb.com/title/tt1234567",
            "imdb_id": "tt1234567",
            "poster": "https://example.com/poster.jpg",
            "is_series": "False",
            "is_episode": "False", 
            "series_info": "",
            "episode_info": "",
            "release_dates": "March 15, 2023",
            "premiere_date": "March 12, 2023",
            "original_air_date": "",
            "budget": "$50M",
            "gross": "$200M",
            "box_office": "Budget: $50M | Gross: $200M",
            "opening_weekend_usa": "$25M"
        }
        
        try:
            preview = template.format(**mock_data)
            await message.reply_text(f"👁️ <b>Template Preview:</b>\n\n{preview}", parse_mode=ParseMode.HTML)
        except KeyError as e:
            await message.reply_text(f"❌ Template error: Unknown placeholder {e}")
        except Exception as e:
            await message.reply_text(f"❌ Template formatting error: {e}")
            
    except Exception as e:
        logger.error(f"Error previewing IMDB template: {e}")
        await message.reply_text("❌ Failed to preview template.")


async def mdl_placeholders_command(client: Client, message: Message):
    """Show all available MyDramaList placeholders."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    placeholders_text = """
📋 <b>MyDramaList Template Placeholders</b>

<b>📺 Basic Information:</b>
• <code>{title}</code> - Drama title
• <code>{complete_title}</code> - Full drama title
• <code>{native_title}</code> - Original language title
• <code>{also_known_as}</code> - Alternative names
• <code>{year}</code> - Release year
• <code>{rating}</code> - User rating
• <code>{link}</code> - MyDramaList URL

<b>📍 Details:</b>
• <code>{country}</code> - Country of origin
• <code>{type}</code> - Content type (Drama/Movie)
• <code>{episodes}</code> - Number of episodes
• <code>{duration}</code> - Episode duration
• <code>{aired}</code> - Air date
• <code>{aired_on}</code> - Broadcasting network
• <code>{original_network}</code> - Original broadcaster
• <code>{content_rating}</code> - Age rating

<b>📊 Stats & Rankings:</b>
• <code>{score}</code> - Overall score
• <code>{ranked}</code> - Ranking position
• <code>{popularity}</code> - Popularity ranking
• <code>{watchers}</code> - Number of watchers
• <code>{favorites}</code> - Times favorited

<b>🎭 Content:</b>
• <code>{synopsis}</code> - Plot summary
• <code>{genres}</code> - Genres with emojis
• <code>{tags}</code> - Drama tags
• <code>{poster}</code> - Poster image URL

<b>📅 Release Info:</b>
• <code>{release_date}</code> - Release/air date

<b>💡 Usage Tips:</b>
• Use HTML formatting: <code>&lt;b&gt;bold&lt;/b&gt;</code>, <code>&lt;i&gt;italic&lt;/i&gt;</code>
• Add emojis for visual appeal
• Keep templates under 1000 characters
• Use <code>{link}</code> at the end for "See more..."

<b>Example:</b>
<pre>
🎭 &lt;b&gt;{title}&lt;/b&gt;
📍 {country} | {episodes} episodes
⭐ Rating: {rating}
🎬 {genres}
📖 {synopsis}
🔗 &lt;a href='{link}'&gt;More details&lt;/a&gt;
</pre>
"""
    await message.reply_text(placeholders_text, parse_mode=ParseMode.HTML)


async def imdb_placeholders_command(client: Client, message: Message):
    """Show all available IMDB placeholders."""
    OWNER_ID = settings.owner_id
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        # 2. Check public mode
        public_setting = await mongo_client.db.settings.find_one(
            {"key": "public_mode"}
        )
        is_public = public_setting.get("value", True) if public_setting else True

        if not is_public:
            # 3. Check authorized users
            auth_user = await mongo_client.db.authorized_users.find_one(
                {"user_id": user_id}
            )
            if not auth_user:
                await message.reply_text(
                    "❌ You are not authorized to use this bot."
                )
                return
    placeholders_text = """
📋 <b>IMDB Template Placeholders</b>

<b>🎬 Basic Information:</b>
• <code>{title}</code> - Movie/show title
• <code>{kind}</code> - Type (movie, tvSeries, etc.)
• <code>{year}</code> - Release year
• <code>{rating}</code> - IMDB rating (1-10)
• <code>{votes}</code> - Number of votes
• <code>{runtime}</code> - Duration
• <code>{imdb_url}</code> - IMDB URL
• <code>{imdb_id}</code> - IMDB ID (tt123456)
• <code>{poster}</code> - Poster image URL

<b>🌍 Production:</b>
• <code>{countries}</code> - Countries of origin
• <code>{languages}</code> - Available languages
• <code>{mpaa}</code> - MPAA rating (PG-13, R, etc.)
• <code>{certificates}</code> - Content certificates

<b>👥 Cast & Crew:</b>
• <code>{cast}</code> - Main cast with characters
• <code>{cast_simple}</code> - Cast names only
• <code>{directors}</code> - Directors
• <code>{writers}</code> - Writers/Screenplay
• <code>{producers}</code> - Producers
• <code>{composers}</code> - Music composers
• <code>{cinematographers}</code> - Cinematographers
• <code>{editors}</code> - Film editors
• <code>{production_designers}</code> - Production designers
• <code>{costume_designers}</code> - Costume designers

<b>📺 Series/Episode Info:</b>
• <code>{is_series}</code> - True if TV series
• <code>{is_episode}</code> - True if episode
• <code>{series_info}</code> - Season information
• <code>{episode_info}</code> - Episode number (S1E1)

<b>📅 Release Information:</b>
• <code>{release_dates}</code> - Release dates
• <code>{premiere_date}</code> - Premiere date
• <code>{original_air_date}</code> - Original air date (for TV)

<b>🎥 Technical Details:</b>
• <code>{aspect_ratios}</code> - Screen aspect ratios
• <code>{sound_mix}</code> - Sound mixing formats
• <code>{color_info}</code> - Color information

<b>💰 Box Office:</b>
• <code>{budget}</code> - Production budget
• <code>{gross}</code> - Gross earnings
• <code>{box_office}</code> - Combined budget/gross
• <code>{opening_weekend_usa}</code> - Opening weekend

<b>🎭 Content:</b>
• <code>{plot}</code> - Plot summary
• <code>{genres}</code> - Genres with emojis

<b>💡 Usage Tips:</b>
• Cast includes character names: "Actor (Character)"
• Use <code>{cast_simple}</code> for names only
• Series show season info, episodes show S1E1 format
• Box office data available for movies only

<b>Example for Movies:</b>
<pre>
🎬 &lt;b&gt;{title}&lt;/b&gt; ({year})
⭐ {rating}/10 ({votes} votes)
🎭 {genres}
🎪 Cast: {cast}
🎬 Directed by: {directors}
💰 {box_office}
📝 {plot}
</pre>

<b>Example for TV Series:</b>
<pre>
📺 &lt;b&gt;{title}&lt;/b&gt; ({year})
⭐ {rating}/10 | {series_info}
🎭 {genres}
📅 Aired: {original_air_date}
🎪 {cast}
📝 {plot}
</pre>
"""
    await message.reply_text(placeholders_text, parse_mode=ParseMode.HTML)