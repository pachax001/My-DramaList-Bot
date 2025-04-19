# inline.py

from bot.logger.logger import logger
from pyrogram import Client
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChosenInlineResult, InlineQueryResult,
)
from bot.utils.drama_utils import filter_dramas, get_drama_details, build_drama_caption
from bot.permissions.use_bot import user_can_use_bot , is_subscribed
from bot.db.user_db import add_or_update_user
from config import FORCE_SUB_CHANNEL_URL
from pyrogram.errors import MediaCaptionTooLong
# -----------------------------------------------------------------------------------
# Inline Query Handler
# -----------------------------------------------------------------------------------
channel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Main Channel", url=FORCE_SUB_CHANNEL_URL)]])
async def handle_inline_query(bot: Client, inline_query: InlineQuery):
    """Handles inline queries."""
    me = await bot.get_me()
    bot_username = me.username
    user_id = inline_query.from_user.id
    username = inline_query.from_user.username or "Unknown"
    full_name = f"{inline_query.from_user.first_name or ''} {inline_query.from_user.last_name or ''}".strip()
    logger.info(f"Inline Query: {inline_query.query}")
    logger.info(f"User ID: {user_id}")

    try:
        if not await user_can_use_bot(user_id):
            results = [
                InlineQueryResultArticle(
                    title="Access Denied ❌",
                    input_message_content=InputTextMessageContent(
                        "You are not authorized to use this bot.\nPlease contact the bot owner."
                    ),
                    id=f"unauth_{user_id}"
                )
            ]
            logger.warning(f"Unauthorized user {user_id} tried to access inline mode.")
            return await inline_query.answer(results, cache_time=0, is_personal=True)
        if not await is_subscribed(bot,user_id):
            results = [
                InlineQueryResultArticle(

                    title="You are not subscribed to my channel",
                    input_message_content=InputTextMessageContent("You are not subscribed to my channel. Join channel and send /start"),
                    id=f"not_subscribed_{user_id}",
                    reply_markup=channel_markup
                )
            ]
            return await inline_query.answer(results, cache_time=0, is_personal=True,switch_pm_text="You are not subscribed to my channel. Click here to join",switch_pm_parameter="start")
        add_or_update_user(user_id, username, full_name)
        query = inline_query.query.strip()
        if not query or len(query) < 2:
            results = [
                InlineQueryResultArticle(
                    title="Enter a keyword...",
                    input_message_content=InputTextMessageContent(
                        "Enter a keyword to search for dramas."
                    ),
                    id=f"noquery_{user_id}"
                )
            ]
            return await inline_query.answer(results,cache_time=0, is_personal=True)
        dramas = filter_dramas(query)
        #logger.info(f"Found dramas for {query} {dramas}")

        if not dramas:
            results = [
                InlineQueryResultArticle(
                    title="No matching dramas found",
                    description="Try a different query.",
                    input_message_content=InputTextMessageContent(
                        "No matching dramas found."
                    ),
                    id=f"nores_{query}_{user_id}"
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

                input_msg_content = InputTextMessageContent(message_text=f"{title}\n\n{drama_link}",disable_web_page_preview=True)

                markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("View Details", url=f"https://t.me/{bot_username}")]]
                )

                result = InlineQueryResultArticle(
                    title=title,
                    description=description,
                    thumb_url=poster,
                    input_message_content=input_msg_content,
                    reply_markup=markup,
                    id=slug,

                )
                results.append(result)

        return await inline_query.answer(results,cache_time=0,is_personal=True)

    except Exception as e:
        logger.error(f"Error in handle_inline_query for query {inline_query.query}: {e}")
        results = [
            InlineQueryResultArticle(
                title="Error Occurred",
                description="Error Occurred. Please try again later.",
                input_message_content=InputTextMessageContent(
                    f"Error occurred for query:{inline_query.query}"
                ),
                id=f"error_search_{user_id}",
            )
        ]
        return await inline_query.answer(results,cache_time=0,is_personal=True)


async def handle_chosen_inline_result(bot: Client, chosen_inline_result: ChosenInlineResult):
    """Handles the selected inline query result."""
    logger.info(f"Chosen Inline Result: {chosen_inline_result.result_id}")

    try:
        user_id = chosen_inline_result.from_user.id
        slug = chosen_inline_result.result_id
        logger.info(f"User {user_id} chose {slug}")

        drama_data = get_drama_details(slug)
        if not drama_data:
            return await bot.send_message(
                chat_id=user_id,
                text="Failed to fetch drama details."
            )


        caption = build_drama_caption(user_id, drama_data, slug)
        poster = drama_data.get("poster")

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚫 Close", callback_data="close_search")]]
        )

        if poster:
            return await bot.send_photo(
                chat_id=user_id,
                photo=poster,
                caption=caption,
                reply_markup=markup
            )
        else:
            return await bot.send_message(
                chat_id=user_id,
                text=caption,
                reply_markup=markup
            )
    except MediaCaptionTooLong as e:
        logger.error(f"MediaCaptionTooLong: {e}")
        return await bot.send_message(
            chat_id=chosen_inline_result.from_user.id,
            text="Failed to fetch drama details. Caption is too long for image. Please reduce caption and try again.",
        )
    except Exception as e:
        logger.error(f"Error in handle_chosen_inline_result: {e}")
        return await bot.send_message(
            chat_id=chosen_inline_result.from_user.id,
            text="An error occurred. Please try again later."
        )
