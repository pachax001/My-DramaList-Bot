import re
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.imdb_utils import build_imdb_caption
from bot.helper.imdb.imdb_details import get_details_by_imdb_id
from bot.permissions.use_bot import user_can_use_bot
from bot.logger.logger import logger
from bot.db.user_db import add_or_update_user
async def handle_imdb_url(client: Client, message: Message):
    """Handles the /url command to fetch drama details from a MyDramaList link."""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")
    add_or_update_user(user_id, username, full_name)
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("Usage: /imdburl IMDB_URL")

    IMDB_link = parts[1].strip()
    logger.info(f"User {user_id} requested URL: {IMDB_link}")

    # Validate MyDramaList URL
    m = re.search(r"tt(\d+)", IMDB_link)
    if not m:
        return await message.reply_text("Invalid IMDb URL!")
    imdb_id = m.group(1)  # "2911666"

    #slug = drama_link.split("/")[-1]
    IMDB_data = get_details_by_imdb_id(imdb_id)
    if not IMDB_data:
        return await message.reply_text("Failed to fetch IMDB details. Please try again later.")

    caption = build_imdb_caption(user_id, IMDB_data)
    poster = IMDB_data.get("poster")

    markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])

    if poster:
        await message.reply_photo(
            photo=poster,
            caption=caption,
            reply_markup=markup
        )
        return None
    else:
        await message.reply_text(caption, reply_markup=markup)
        return None
