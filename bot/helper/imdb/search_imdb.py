from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, FORCE_SUB_CHANNEL_URL
from bot.permissions.use_bot import user_can_use_bot, is_subscribed
from bot.db.user_db import add_or_update_user
from bot.logger.logger import logger
from bot.utils.imdb_utils import filter_imdb, build_imdb_caption
from bot.helper.imdb.imdb_details import get_details_by_imdb_id
from pyrogram.errors import MediaCaptionTooLong
PAGE_SIZE = 10
channel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Main Channel", url=FORCE_SUB_CHANNEL_URL)]])
async def search_imdb(client: Client, message: Message):
    user_id = message.from_user.id
    if not await user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    if not await is_subscribed(client,user_id):
        return await message.reply_text(
            text="You have not subscribed to my channel.. Subscribe and send /start again",
            reply_markup=channel_markup)
    # parse out the query
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("Usage: /imdb <keyword>")
    query = parts[1].strip()

    processing_message = await message.reply_text("Processing Your Request...⚙️")

    # fetch & store full list in memory (or re-query each time)
    all_results = filter_imdb(query)
    if not all_results:
        return await processing_message.edit_text("No IMDb results found.")

    # show page 1
    await processing_message.delete()
    return await _show_page(message, query, all_results, page=1)



async def imdb_pagination_callback(client, callback_query):
    # callback_data format: imdb:myquery:page
    _, query, page_str = callback_query.data.split(":", 2)
    page = int(page_str)

    all_results = filter_imdb(query)
    # safety check
    if not all_results:
        return await callback_query.message.edit_text("No results found.")

    await _show_page(callback_query.message, query, all_results, page, edit=True)
    return await callback_query.answer()  # removes the “⏳” loading state



async def _show_page(msg_or_event, query, all_results, page, edit=False):
    """
    msg_or_event: either a Message or CallbackQuery.message
    query: the search keyword
    all_results: full list of Movie objects
    page: 1-based page number
    edit: whether to edit existing message (True) or send new (False)
    """
    start = (page - 1) * PAGE_SIZE
    end   = start + PAGE_SIZE
    page_items = all_results[start:end]

    keyboard = []
    for movie in page_items:
        slug = movie.movieID
        title = movie.get('title') or "Unknown Title"
        keyboard.append([
            InlineKeyboardButton(title, callback_data=f"imdbdetails_{slug}")
        ])

    # build Prev/Next row
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous",
                                 callback_data=f"imdb:{query}:{page-1}")
        )
    if end < len(all_results):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️",
                                 callback_data=f"imdb:{query}:{page+1}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # close button
    keyboard.append([InlineKeyboardButton("🚫 Close", callback_data="close_search")])

    markup = InlineKeyboardMarkup(keyboard)
    text   = f"Results for **{query}** (page {page} of {((len(all_results)-1)//PAGE_SIZE)+1}):"

    if edit:
        await msg_or_event.edit_text(text, reply_markup=markup)
    else:
        await msg_or_event.reply_text(text, reply_markup=markup)


async def imdb_details_callback(bot: Client, update: CallbackQuery):
    try:
        user_id = update.from_user.id
        imdb_id = update.data.split("_", 1)[1]
        logger.info(f"User {user_id} requested imdb details for slug: {imdb_id}")

        imdb_data = get_details_by_imdb_id(imdb_id)
        logger.info(f"Retrieved imdb details for slug: {imdb_id}")
        logger.info(f"Found {imdb_data} imdb details")

        if not imdb_data:
            await bot.send_message(
                chat_id=update.message.chat.id,
                text="Failed to fetch imdb details."
            )
            return
        caption =build_imdb_caption(user_id, imdb_data)
        poster = imdb_data.get("poster")
        logger.info(f"Found poster {poster}")
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
        if update.message.reply_to_message:
            await update.message.reply_to_message.delete()
        return await update.message.delete()
    except MediaCaptionTooLong as e:
        logger.error(f"MediaCaptionTooLong: {e}")
        return await bot.send_message(text=f"Failed to fetch IMDB details. Caption is too long for image. Please reduce caption and try again.",chat_id=update.message.chat.id)
    except Exception as e:
        logger.error(f"Error in imdb_details_callback: {e}")
        return await bot.send_message(
            chat_id=update.message.chat.id,
            text="An error occurred. Please try again later."
        )

