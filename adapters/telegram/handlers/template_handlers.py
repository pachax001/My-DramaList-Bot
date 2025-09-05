"""Template management handlers."""

from pyrogram import Client
from pyrogram.types import Message
from infra.logging import get_logger
from infra.db import mongo_client

logger = get_logger(__name__)


async def set_template_command(client: Client, message: Message):
    """Set MyDramaList template for user."""
    user_id = message.from_user.id
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "**Usage:** `/setmdltemplate <template>` or reply to a template message\n\n"
                "**Example Template:**\n"
                "```\n"
                "🎭 <b>{title}</b>\n"
                "📍 {country} | Episodes: {episodes}\n"
                "⭐ Rating: {rating}\n"
                "🎬 Genres: {genres}\n"
                "📖 {synopsis}\n"
                "```\n\n"
                "**Popular Placeholders:**\n"
                "• `{title}` - Drama title\n"
                "• `{rating}` - User rating\n"
                "• `{synopsis}` - Plot summary\n"
                "• `{country}` - Country of origin\n"
                "• `{episodes}` - Number of episodes\n"
                "• `{genres}` - Genres with emojis\n"
                "• `{year}` - Release year\n\n"
                "Use /mdlplaceholders to see all available placeholders!"
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
        
        logger.info(f"User {user_id} set MDL template")
        await message.reply_text("✅ MyDramaList template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting MDL template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_template_command(client: Client, message: Message):
    """Get user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        
        if template_doc:
            template = template_doc.get("template", "")
            await message.reply_text(f"📝 Your current MyDramaList template:\n\n`{template}`")
        else:
            await message.reply_text("ℹ️ You don't have a custom MyDramaList template set.")
            
    except Exception as e:
        logger.error(f"Error getting MDL template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_template_command(client: Client, message: Message):
    """Remove user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        result = await mongo_client.db.mdl_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"User {user_id} removed MDL template")
            await message.reply_text("✅ MyDramaList template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have a MyDramaList template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing MDL template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_template_command(client: Client, message: Message):
    """Preview user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        
        if not template_doc:
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
            preview = template_doc["template"].format(**mock_data)
            await message.reply_text(f"👁️ **Template Preview:**\n\n{preview}")
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
    user_id = message.from_user.id
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "**Usage:** `/setimdbtemplate <template>` or reply to a template message\n\n"
                "**Example Template:**\n"
                "```\n"
                "🎬 <b>{title}</b> ({year})\n"
                "⭐ {rating}/10 ({votes} votes)\n"
                "🎭 Cast: {cast}\n"
                "🎬 Directors: {directors}\n"
                "📝 {plot}\n"
                "```\n\n"
                "**Popular Placeholders:**\n"
                "• `{title}` - Movie/show title\n"
                "• `{year}` - Release year\n"
                "• `{rating}` - IMDB rating\n"
                "• `{votes}` - Number of votes\n"
                "• `{cast}` - Main cast with characters\n"
                "• `{directors}` - Directors\n"
                "• `{plot}` - Plot summary\n"
                "• `{genres}` - Genres with emojis\n\n"
                "Use /imdbplaceholders to see all 50+ available placeholders!"
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
        
        logger.info(f"User {user_id} set IMDB template")
        await message.reply_text("✅ IMDB template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting IMDB template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_imdb_template_command(client: Client, message: Message):
    """Get user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        
        if template_doc:
            template = template_doc.get("template", "")
            await message.reply_text(f"📝 Your current IMDB template:\n\n`{template}`")
        else:
            await message.reply_text("ℹ️ You don't have a custom IMDB template set.")
            
    except Exception as e:
        logger.error(f"Error getting IMDB template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_imdb_template_command(client: Client, message: Message):
    """Remove user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        result = await mongo_client.db.imdb_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"User {user_id} removed IMDB template")
            await message.reply_text("✅ IMDB template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have an IMDB template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing IMDB template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_imdb_template_command(client: Client, message: Message):
    """Preview user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        
        if not template_doc:
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
            preview = template_doc["template"].format(**mock_data)
            await message.reply_text(f"👁️ **Template Preview:**\n\n{preview}")
        except KeyError as e:
            await message.reply_text(f"❌ Template error: Unknown placeholder {e}")
        except Exception as e:
            await message.reply_text(f"❌ Template formatting error: {e}")
            
    except Exception as e:
        logger.error(f"Error previewing IMDB template: {e}")
        await message.reply_text("❌ Failed to preview template.")


async def mdl_placeholders_command(client: Client, message: Message):
    """Show all available MyDramaList placeholders."""
    placeholders_text = """
📋 **MyDramaList Template Placeholders**

**📺 Basic Information:**
• `{title}` - Drama title
• `{complete_title}` - Full drama title
• `{native_title}` - Original language title
• `{also_known_as}` - Alternative names
• `{year}` - Release year
• `{rating}` - User rating
• `{link}` - MyDramaList URL

**📍 Details:**
• `{country}` - Country of origin
• `{type}` - Content type (Drama/Movie)
• `{episodes}` - Number of episodes
• `{duration}` - Episode duration
• `{aired}` - Air date
• `{aired_on}` - Broadcasting network
• `{original_network}` - Original broadcaster
• `{content_rating}` - Age rating

**📊 Stats & Rankings:**
• `{score}` - Overall score
• `{ranked}` - Ranking position
• `{popularity}` - Popularity ranking
• `{watchers}` - Number of watchers
• `{favorites}` - Times favorited

**🎭 Content:**
• `{synopsis}` - Plot summary
• `{genres}` - Genres with emojis
• `{tags}` - Drama tags
• `{poster}` - Poster image URL

**📅 Release Info:**
• `{release_date}` - Release/air date

**💡 Usage Tips:**
• Use HTML formatting: `<b>bold</b>`, `<i>italic</i>`
• Add emojis for visual appeal
• Keep templates under 1000 characters
• Use `{link}` at the end for "See more..."

**Example:**
```
🎭 <b>{title}</b>
📍 {country} | {episodes} episodes
⭐ Rating: {rating}
🎬 {genres}
📖 {synopsis}
🔗 <a href='{link}'>More details</a>
```
"""
    await message.reply_text(placeholders_text)


async def imdb_placeholders_command(client: Client, message: Message):
    """Show all available IMDB placeholders."""
    placeholders_text = """
📋 **IMDB Template Placeholders**

**🎬 Basic Information:**
• `{title}` - Movie/show title
• `{kind}` - Type (movie, tvSeries, etc.)
• `{year}` - Release year
• `{rating}` - IMDB rating (1-10)
• `{votes}` - Number of votes
• `{runtime}` - Duration
• `{imdb_url}` - IMDB URL
• `{imdb_id}` - IMDB ID (tt123456)
• `{poster}` - Poster image URL

**🌍 Production:**
• `{countries}` - Countries of origin
• `{languages}` - Available languages
• `{mpaa}` - MPAA rating (PG-13, R, etc.)
• `{certificates}` - Content certificates

**👥 Cast & Crew:**
• `{cast}` - Main cast with characters
• `{cast_simple}` - Cast names only
• `{directors}` - Directors
• `{writers}` - Writers/Screenplay
• `{producers}` - Producers
• `{composers}` - Music composers
• `{cinematographers}` - Cinematographers
• `{editors}` - Film editors
• `{production_designers}` - Production designers
• `{costume_designers}` - Costume designers

**📺 Series/Episode Info:**
• `{is_series}` - True if TV series
• `{is_episode}` - True if episode
• `{series_info}` - Season information
• `{episode_info}` - Episode number (S1E1)

**📅 Release Information:**
• `{release_dates}` - Release dates
• `{premiere_date}` - Premiere date
• `{original_air_date}` - Original air date (for TV)

**🎥 Technical Details:**
• `{aspect_ratios}` - Screen aspect ratios
• `{sound_mix}` - Sound mixing formats
• `{color_info}` - Color information

**💰 Box Office:**
• `{budget}` - Production budget
• `{gross}` - Gross earnings
• `{box_office}` - Combined budget/gross
• `{opening_weekend_usa}` - Opening weekend

**🎭 Content:**
• `{plot}` - Plot summary
• `{genres}` - Genres with emojis

**💡 Usage Tips:**
• Cast includes character names: "Actor (Character)"
• Use `{cast_simple}` for names only
• Series show season info, episodes show S1E1 format
• Box office data available for movies only

**Example for Movies:**
```
🎬 <b>{title}</b> ({year})
⭐ {rating}/10 ({votes} votes)
🎭 {genres}
🎪 Cast: {cast}
🎬 Directed by: {directors}
💰 {box_office}
📝 {plot}
```

**Example for TV Series:**
```
📺 <b>{title}</b> ({year})
⭐ {rating}/10 | {series_info}
🎭 {genres}
📅 Aired: {original_air_date}
🎪 {cast}
📝 {plot}
```
"""
    await message.reply_text(placeholders_text)