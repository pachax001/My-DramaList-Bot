import re
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.imdb_utils import build_imdb_caption
from bot.helper.imdb.imdb_details import get_details_by_imdb_id
from bot.permissions.use_bot import user_can_use_bot, is_subscribed
from bot.logger.logger import logger
from bot.db.user_db import add_or_update_user
from pyrogram.errors import MediaCaptionTooLong
channel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Main Channel", url="https://t.me/kdramaworld_ongoing")]])
async def handle_imdb_url(client: Client, message: Message):
    """Handles the /url command to fetch drama details from a MyDramaList link."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        if not await user_can_use_bot(user_id):
            return await message.reply_text("You are not authorized to use this bot.")
        if not await is_subscribed(client,user_id):
            return await message.reply_text(
                text="You have not subscribed to my channel.. Subscribe and send /start again",
                reply_markup=channel_markup)
        add_or_update_user(user_id, username, full_name)
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            return await message.reply_text("Usage: /imdburl IMDB_URL")

        IMDB_link = parts[1].strip()
        logger.info(f"User {user_id} requested URL: {IMDB_link}")

        # Validate MyDramaList URL
        processing_message = await message.reply_text("Processing Your Request...⚙️")
        m = re.search(r"tt(\d+)", IMDB_link)

        if not m:
            return await processing_message.edit_text("Invalid IMDb URL!")
        imdb_id = m.group(1)  # "2911666"

        #slug = drama_link.split("/")[-1]
        IMDB_data = get_details_by_imdb_id(imdb_id)
        if not IMDB_data:
            return await processing_message.edit_text("Failed to fetch IMDB details. Please try again later.")

        caption = build_imdb_caption(user_id, IMDB_data)
        poster = IMDB_data.get("poster")

        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])
        await processing_message.delete()
        if poster:
            return await message.reply_photo(
                photo=poster,
                caption=caption,
                reply_markup=markup
            )

        else:
            return await message.reply_text(caption, reply_markup=markup)
    except MediaCaptionTooLong as e:
        logger.error(f"MediaCaptionTooLong: {e}")
        return await message.reply_text(
            f"Failed to fetch IMDB details. Caption is too long for image. Please reduce caption and try again.")
    except Exception as e:
        logger.error(f"Error in drama_details_callback: {e}")
        return await message.reply_text("Error Occurred. Please try again later.")

