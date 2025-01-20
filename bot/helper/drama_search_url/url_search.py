import re
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.drama_utils import get_drama_details, build_drama_caption
from bot.permissions.use_bot import user_can_use_bot
from bot.logger.logger import logger
from bot.db.user_db import add_or_update_user
async def handle_drama_url(client: Client, message: Message):
    """Handles the /url command to fetch drama details from a MyDramaList link."""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")
    add_or_update_user(user_id, username, full_name)
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("Usage: /url MyDramaList_URL")

    drama_link = parts[1].strip()
    logger.info(f"User {user_id} requested URL: {drama_link}")

    # Validate MyDramaList URL
    mydramalist_regex = r"https://mydramalist.com/\d+-\S+"
    if not re.match(mydramalist_regex, drama_link):
        return await message.reply_text("Invalid MyDramaList URL format. Please provide a valid URL.")

    slug = drama_link.split("/")[-1]
    drama_data = get_drama_details(slug)
    if not drama_data:
        return await message.reply_text("Failed to fetch drama details. Please try again later.")

    caption = build_drama_caption(user_id, drama_data, slug)
    poster = drama_data.get("poster")

    markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Close", callback_data="close_search")]])

    if poster:
        await message.reply_photo(
            photo=poster,
            caption=caption,
            reply_markup=markup
        )
    else:
        await message.reply_text(caption, reply_markup=markup)
