from bot.logger.logger import logger
from pyrogram import Client
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.drama_utils import filter_dramas, get_drama_details, build_drama_caption
from bot.permissions.use_bot import user_can_use_bot
from bot.db.user_db import add_or_update_user

async def search_dramas_command(client: Client, message: Message):
    """Handles the /s <query> command for searching dramas."""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")
    add_or_update_user(user_id, username, full_name)
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("Usage: /s search_query")

    query = parts[1].strip()
    logger.info(f"User {user_id} is searching for '{query}'")
    dramas = filter_dramas(query)

    if not dramas:
        return await message.reply_text("No dramas found for that query.")

    # Build button list
    keyboard = []
    for drama in dramas:
        slug = drama["slug"]
        btn_text = f"{drama['title']} ({drama['year']})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"details_{slug}")])

    keyboard.append([InlineKeyboardButton("🚫 Close", callback_data="close_search")])

    await message.reply_text(
        "Here are the search results. Click on a drama for more info:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def drama_details_callback(bot: Client, update: CallbackQuery):
    """Handles drama details display when an inline button is clicked."""
    try:
        user_id = update.from_user.id
        slug = update.data.split("_", 1)[1]
        logger.info(f"User {user_id} requested drama details for slug: {slug}")

        drama_data = get_drama_details(slug)
        if not drama_data:
            await bot.send_message(
                chat_id=update.message.chat.id,
                text="Failed to fetch drama details."
            )
            return

        caption = build_drama_caption(user_id, drama_data, slug)
        poster = drama_data.get("poster")

        # Prepare the buttons
        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚫 Close", callback_data="close_search")]]
        )

        if poster:
            await bot.send_photo(
                chat_id=update.message.chat.id,
                photo=poster,
                caption=caption,
                reply_markup=markup
            )
        else:
            await bot.send_message(
                chat_id=update.message.chat.id,
                text=caption,
                reply_markup=markup
            )

        # Clean up the old messages if needed
        if update.message.reply_to_message:
            await update.message.reply_to_message.delete()
        await update.message.delete()

    except Exception as e:
        logger.error(f"Error in drama_details_callback: {e}")
        await bot.send_message(
            chat_id=update.message.chat.id,
            text="An error occurred. Please try again later."
        )


async def close_search_results(bot: Client, query: CallbackQuery):
    """Handles closing of search result messages."""
    try:
        await query.answer()
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error closing search results: {e}")
