# inline.py

from bot.logger.logger import logger
from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChosenInlineResult,
)
from bot.utils.drama_utils import filter_dramas, get_drama_details, build_drama_caption
from bot.permissions.use_bot import user_can_use_bot
from bot.db.user_db import add_or_update_user

# -----------------------------------------------------------------------------------
# Inline Query Handler
# -----------------------------------------------------------------------------------

async def handle_inline_query(bot: Client, inline_query: InlineQuery):
    """Handles inline queries."""
    user_id = inline_query.from_user.id
    username = inline_query.from_user.username or "Unknown"
    full_name = f"{inline_query.from_user.first_name or ''} {inline_query.from_user.last_name or ''}".strip()
    logger.info(f"Inline Query: {inline_query.query}")
    logger.info(f"User ID: {user_id}")

    try:
        if not user_can_use_bot(user_id):
            results = [
                InlineQueryResultArticle(
                    title="Access Denied ❌",
                    input_message_content=InputTextMessageContent(
                        "You are not authorized to use this bot.\nPlease contact the bot owner."
                    ),
                    id="unauthorized"
                )
            ]
            await inline_query.answer(results, cache_time=0, is_personal=True)
            logger.warning(f"Unauthorized user {user_id} tried to access inline mode.")
            return
        add_or_update_user(user_id, username, full_name)
        query = inline_query.query.strip()
        if not query or len(query) < 2:
            results = [
                InlineQueryResultArticle(
                    title="Enter a keyword...",
                    input_message_content=InputTextMessageContent(
                        "Enter a keyword to search for dramas."
                    ),
                    id="no_query"
                )
            ]
            await inline_query.answer(results)
            return

        dramas = filter_dramas(query)
        if not dramas:
            results = [
                InlineQueryResultArticle(
                    title="No matching dramas found",
                    description="Try a different query.",
                    input_message_content=InputTextMessageContent(
                        "No matching dramas found."
                    ),
                    id="no_results"
                )
            ]
        else:
            results = []
            for drama in dramas:
                slug = drama["slug"]
                title = f"{drama['title']} ({drama['year']})"
                description = f"Type: {drama.get('type','N/A')} | Episodes: {drama.get('series','N/A')}"
                poster = drama["thumb"]
                drama_link = f"https://mydramalist.com/{slug}"

                input_msg_content = InputTextMessageContent(f"{title}\n\n{drama_link}")

                markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("View Details", url=f"https://t.me/{bot.me.username}")]]
                )

                result = InlineQueryResultArticle(
                    title=title,
                    description=description,
                    thumb_url=poster,
                    input_message_content=input_msg_content,
                    reply_markup=markup,
                    id=slug
                )
                results.append(result)

        await inline_query.answer(results)

    except Exception as e:
        logger.error(f"Error in handle_inline_query: {e}")

async def handle_chosen_inline_result(bot: Client, chosen_inline_result: ChosenInlineResult):
    """Handles the selected inline query result."""
    logger.info(f"Chosen Inline Result: {chosen_inline_result.result_id}")

    try:
        user_id = chosen_inline_result.from_user.id
        slug = chosen_inline_result.result_id
        logger.info(f"User {user_id} chose {slug}")

        drama_data = get_drama_details(slug)
        if not drama_data:
            await bot.send_message(
                chat_id=user_id,
                text="Failed to fetch drama details."
            )
            return

        caption = build_drama_caption(user_id, drama_data, slug)
        poster = drama_data.get("poster")

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚫 Close", callback_data="close_search")]]
        )

        if poster:
            await bot.send_photo(
                chat_id=user_id,
                photo=poster,
                caption=caption,
                reply_markup=markup
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=caption,
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Error in handle_chosen_inline_result: {e}")
        await bot.send_message(
            chat_id=chosen_inline_result.from_user.id,
            text="An error occurred. Please try again later."
        )
