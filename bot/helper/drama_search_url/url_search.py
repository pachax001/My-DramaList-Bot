import re

import asyncio
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.drama_utils import get_drama_details, build_drama_caption
from bot.permissions.use_bot import user_can_use_bot, is_subscribed
from bot.logger.logger import logger
from bot.db.user_db import add_or_update_user
from config import FORCE_SUB_CHANNEL_URL
from pyrogram.errors import MediaCaptionTooLong
channel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Main Channel", url=FORCE_SUB_CHANNEL_URL)]])

async def handle_drama_url(client: Client, message: Message):
    """Handles the /mdlurl command to fetch drama details from a MyDramaList link."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        if not await user_can_use_bot(user_id):
            return await message.reply_text("You are not authorized to use this bot.")
        if not await is_subscribed(client,user_id):
            return await message.reply_text(text="You have not subscribed to my channel.. Subscribe and send /start again",reply_markup=channel_markup)
        add_or_update_user(user_id, username, full_name)
        # Validate MyDramaList URL
        processing_message = await message.reply_text("Processing Your Request...⚙️")
        await asyncio.sleep(2)
        if message.reply_to_message and message.reply_to_message.text:
            replied_text = message.reply_to_message.text or ""
            mydramalist_regex = r"https://mydramalist.com/\d+-\S+"
            match = re.search(mydramalist_regex, replied_text)
            if match:
                drama_link = match.group(0)
            else:
                return await processing_message.edit_text("Invalid MyDramaList URL format. Please provide a valid URL.")
        else:
            parts = message.text.split(" ", 1)
            if len(parts) < 2:
                return await processing_message.edit_text("Usage: /mdlurl MyDramaList_URL or reply to the url with the command")
            drama_link = parts[1].strip()
            mydramalist_regex = r"https://mydramalist.com/\d+-\S+"
            if not re.match(mydramalist_regex, drama_link):
                return await processing_message.edit_text("Invalid MyDramaList URL format. Please provide a valid URL.")
        logger.info(f"User {user_id} requested URL: {drama_link}")
        slug = drama_link.split("/")[-1]
        drama_data = get_drama_details(slug)
        if not drama_data:
            return await processing_message.edit_text("Failed to fetch drama details. Please try again later.")

        caption = build_drama_caption(user_id, drama_data, slug)
        poster = drama_data.get("poster")

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
        logger.error(f"MediaCaptionTooLong error: {e}")
        return await message.reply_text(f"Failed to fetch drama details. Caption is too long for image. Please reduce caption and try again.")
    except Exception as e:
        logger.error(f"Failed to fetch drama details. Error: {e}")
        return await message.reply_text(f"Failed to fetch drama details. Please try again later.")