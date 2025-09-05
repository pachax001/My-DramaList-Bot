"""Search command handlers."""

import uuid

from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from adapters.imdb import imdb_adapter
from adapters.mydramalist import mydramalist_adapter
from domain.services import template_service
from infra.db import mongo_client
from infra.logging import get_logger, set_correlation_id
from infra.ratelimit import user_limiter

logger = get_logger(__name__)


async def search_dramas_command(client: Client, message: Message) -> None:
    """Handle /mdl command for MyDramaList search."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = message.from_user.id
    
    # Apply user rate limiting first
    if not await user_limiter.is_allowed(f"user:{user_id}", limit=10, window=60):
        await message.reply_text(
            "🚦 You're sending requests too quickly. Please wait a moment before trying again."
        )
        return
    
    # Check authorization (simplified)
    public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
    is_public = public_setting.get("value", True) if public_setting else True
    
    if not is_public:
        # Check if user is authorized
        auth_user = await mongo_client.db.authorized_users.find_one({"user_id": user_id})
        if not auth_user:
            await message.reply_text("❌ You are not authorized to use this bot.")
            return
    
    # Parse query
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.reply_text("Usage: /mdl <search_query>")
        return
    
    query = parts[1].strip()
    logger.info(f"User {user_id} searching MDL for: {query}")
    
    processing_msg = await message.reply_text("🔍 Searching MyDramaList...")
    
    try:
        # Search dramas
        dramas = await mydramalist_adapter.search_dramas(query)
        
        if not dramas:
            await processing_msg.edit_text("❌ No dramas found for that query.")
            return
        
        # Build keyboard
        keyboard = []
        for drama in dramas[:10]:  # Limit to 10 results
            slug = drama.get("slug", "")
            title = drama.get("title", "Unknown")
            year = drama.get("year", "")
            btn_text = f"{title} ({year})" if year else title
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"details_{slug}")])
        
        keyboard.append([InlineKeyboardButton("🚫 Close", callback_data="close_search")])
        
        await processing_msg.edit_text(
            f"🎭 Found {len(dramas)} dramas for **{query}**:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in MDL search: {e}")
        await processing_msg.edit_text("❌ Search failed. Please try again later.")


async def search_imdb(client: Client, message: Message) -> None:
    """Handle /imdb command for IMDB search."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = message.from_user.id
    
    # Apply user rate limiting first
    if not await user_limiter.is_allowed(f"user:{user_id}", limit=10, window=60):
        await message.reply_text(
            "🚦 You're sending requests too quickly. Please wait a moment before trying again."
        )
        return
    
    # Check authorization (simplified)
    public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
    is_public = public_setting.get("value", True) if public_setting else True
    
    if not is_public:
        auth_user = await mongo_client.db.authorized_users.find_one({"user_id": user_id})
        if not auth_user:
            await message.reply_text("❌ You are not authorized to use this bot.")
            return
    
    # Parse query
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.reply_text("Usage: /imdb <search_query>")
        return
    
    query = parts[1].strip()
    logger.info(f"User {user_id} searching IMDB for: {query}")
    
    processing_msg = await message.reply_text("🔍 Searching IMDB...")
    
    try:
        # Search movies
        movies = await imdb_adapter.search_movies(query)
        
        if not movies:
            await processing_msg.edit_text("❌ No movies found for that query.")
            return
        
        # Build keyboard
        keyboard = []
        for movie in movies[:10]:  # Limit to 10 results
            movie_id = movie.get("id", "")
            title = movie.get("title", "Unknown")
            year = movie.get("year", "")
            btn_text = f"{title} ({year})" if year else title
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"imdbdetails_{movie_id}")])
        
        keyboard.append([InlineKeyboardButton("🚫 Close", callback_data="close_search")])
        
        await processing_msg.edit_text(
            f"🎬 Found {len(movies)} movies for **{query}**:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in IMDB search: {e}")
        await processing_msg.edit_text("❌ Search failed. Please try again later.")


async def drama_details_callback(client: Client, callback_query: CallbackQuery) -> None:
    """Handle drama details callback."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = callback_query.from_user.id
    
    try:
        # Extract slug from callback data
        slug = callback_query.data.split("_", 1)[1]
        logger.info(f"User {user_id} requested drama details for: {slug}")
        
        # Get drama details
        drama_data = await mydramalist_adapter.get_drama_details(slug)
        
        if not drama_data:
            await callback_query.answer("❌ Failed to get drama details.", show_alert=True)
            return
        
        # Get user template
        user_template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        user_template = user_template_doc.get("template") if user_template_doc else None
        
        # Build caption
        caption = template_service.build_mdl_caption(drama_data, slug, user_template)
        
        # Create close button
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])
        
        # Send details
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=caption,
            reply_markup=markup
        )
        
        # Delete original message
        await callback_query.message.delete()
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in drama details: {e}")
        await callback_query.answer("❌ Failed to get drama details.", show_alert=True)


async def imdb_details_callback(client: Client, callback_query: CallbackQuery) -> None:
    """Handle IMDB details callback."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = callback_query.from_user.id
    
    try:
        # Extract movie ID from callback data
        movie_id = callback_query.data.split("_", 1)[1]
        logger.info(f"User {user_id} requested IMDB details for: {movie_id}")
        
        # Get movie details
        movie_data = await imdb_adapter.get_movie_details(movie_id)
        
        if not movie_data:
            await callback_query.answer("❌ Failed to get movie details.", show_alert=True)
            return
        
        # Get user template
        user_template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        user_template = user_template_doc.get("template") if user_template_doc else None
        
        # Build caption
        caption = template_service.build_imdb_caption(movie_data, user_template)
        
        # Create close button
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])
        
        # Send details
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=caption,
            reply_markup=markup
        )
        
        # Delete original message
        await callback_query.message.delete()
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in IMDB details: {e}")
        await callback_query.answer("❌ Failed to get movie details.", show_alert=True)


async def close_search_results(client: Client, callback_query: CallbackQuery) -> None:
    """Handle close search results callback."""
    try:
        await callback_query.message.delete()
        await callback_query.answer("🚫 Search results closed.")
    except Exception as e:
        logger.error(f"Error closing search results: {e}")
        await callback_query.answer()


async def handle_drama_url(client: Client, message: Message) -> None:
    """Handle /mdlurl command for MyDramaList URL search."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = message.from_user.id
    
    # Apply user rate limiting first
    if not await user_limiter.is_allowed(f"user:{user_id}", limit=10, window=60):
        await message.reply_text(
            "🚦 You're sending requests too quickly. Please wait a moment before trying again."
        )
        return
    
    # Check authorization (simplified)
    public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
    is_public = public_setting.get("value", True) if public_setting else True
    
    if not is_public:
        # Check if user is authorized
        auth_user = await mongo_client.db.authorized_users.find_one({"user_id": user_id})
        if not auth_user:
            await message.reply_text("❌ You are not authorized to use this bot.")
            return
    
    # Parse URL
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.reply_text(
            "Usage: /mdlurl <mydramalist_url>\n\n"
            "Example: /mdlurl https://mydramalist.com/12345-drama-name"
        )
        return
    
    url = parts[1].strip()
    logger.info(f"User {user_id} requesting MDL URL: {url}")
    
    processing_msg = await message.reply_text("🔍 Processing MyDramaList URL...")
    
    try:
        # Get drama details from URL
        drama_data = await mydramalist_adapter.get_drama_by_url(url)
        
        if not drama_data:
            await processing_msg.edit_text("❌ Could not retrieve drama details from this URL. Please check the URL and try again.")
            return
        
        # Extract slug for callback data
        slug = mydramalist_adapter.extract_slug_from_url(url)
        if not slug:
            slug = "unknown"
        
        # Get user template
        user_template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        user_template = user_template_doc.get("template") if user_template_doc else None
        
        # Build caption
        caption = template_service.build_mdl_caption(drama_data, slug, user_template)
        
        # Create close button
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])
        
        # Send details
        await processing_msg.edit_text(caption, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error in MDL URL processing: {e}")
        await processing_msg.edit_text("❌ Failed to process URL. Please try again later.")


async def handle_imdb_url(client: Client, message: Message) -> None:
    """Handle /imdburl command for IMDB URL search."""
    set_correlation_id(str(uuid.uuid4()))
    user_id = message.from_user.id
    
    # Apply user rate limiting first
    if not await user_limiter.is_allowed(f"user:{user_id}", limit=10, window=60):
        await message.reply_text(
            "🚦 You're sending requests too quickly. Please wait a moment before trying again."
        )
        return
    
    # Check authorization (simplified)
    public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
    is_public = public_setting.get("value", True) if public_setting else True
    
    if not is_public:
        auth_user = await mongo_client.db.authorized_users.find_one({"user_id": user_id})
        if not auth_user:
            await message.reply_text("❌ You are not authorized to use this bot.")
            return
    
    # Parse URL
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.reply_text(
            "Usage: /imdburl <imdb_url>\n\n"
            "Example: /imdburl https://www.imdb.com/title/tt1234567/"
        )
        return
    
    url = parts[1].strip()
    logger.info(f"User {user_id} requesting IMDB URL: {url}")
    
    processing_msg = await message.reply_text("🔍 Processing IMDB URL...")
    
    try:
        # Get movie details from URL
        movie_data = await imdb_adapter.get_movie_by_url(url)
        
        if not movie_data:
            await processing_msg.edit_text("❌ Could not retrieve movie details from this URL. Please check the URL and try again.")
            return
        
        # Get user template
        user_template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        user_template = user_template_doc.get("template") if user_template_doc else None
        
        # Build caption
        caption = template_service.build_imdb_caption(movie_data, user_template)
        
        # Create close button
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])
        
        # Send details
        await processing_msg.edit_text(caption, reply_markup=markup)
        
    except Exception as e:
        logger.error(f"Error in IMDB URL processing: {e}")
        await processing_msg.edit_text("❌ Failed to process URL. Please try again later.")


async def imdb_pagination_callback(client: Client, callback_query: CallbackQuery) -> None:
    """Handle IMDB pagination."""
    await callback_query.answer("🚧 Pagination coming soon!")


# Inline handlers (placeholders)
async def handle_inline_query(client: Client, inline_query) -> None:
    """Handle inline queries."""
    pass


async def handle_chosen_inline_result(client: Client, chosen_inline_result) -> None:
    """Handle chosen inline results."""
    pass