from pyrogram import Client, filters
from pyrogram.handlers import (
    MessageHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    CallbackQueryHandler
)

from config import BOT_TOKEN, API_ID, API_HASH, OWNER_ID
from bot.helper.user_management.user import authorize_cmd, unauthorize_cmd, list_users_cmd
from bot.helper.helper_commands.helper_commands import start_command, send_log, help_command,user_stats_command,set_public_mode_command,manual_broadcast_command
from bot.helper.inline_query.inline_search import handle_inline_query, handle_chosen_inline_result
from bot.helper.search_drama_callback_query.callback_query import (
    search_dramas_command,
    drama_details_callback,
    close_search_results
)
from bot.helper.drama_search_url.url_search import handle_drama_url
from bot.helper.template_management.template_handler import set_template_command, get_template_command, remove_template_command,preview_template_command
from bot.logger.logger import logger
from config import initialize_settings


initialize_settings()

# -------------------------------------------------------------------
# Bot Initialization
# -------------------------------------------------------------------
app = Client(
    "mydramalist_bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)



# async def start_bot():
#     logger.info("Starting bot...")
#     await set_commands()
#     logger.info("Bot is running...")
    

# -------------------------------------------------------------------
# Handlers: Authorization (Owner only)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        authorize_cmd,
        filters.command("authorize", prefixes="/") & filters.user(OWNER_ID)
    )
)
app.add_handler(
    MessageHandler(
        unauthorize_cmd,
        filters.command("unauthorize", prefixes="/") & filters.user(OWNER_ID)
    )
)
app.add_handler(
    MessageHandler(
        list_users_cmd,
        filters.command("users", prefixes="/") & filters.user(OWNER_ID)
    )
)


# -------------------------------------------------------------------
# Handler: /start
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        start_command,
        filters.command("start", prefixes="/")
    )
)


# -------------------------------------------------------------------
# Inline Query Handler
# -------------------------------------------------------------------
app.add_handler(
    InlineQueryHandler(handle_inline_query)
)


# -------------------------------------------------------------------
# Chosen Inline Result Handler
# -------------------------------------------------------------------
app.add_handler(
    ChosenInlineResultHandler(handle_chosen_inline_result)
)


# -------------------------------------------------------------------
# Handler: /s (Search Dramas)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        search_dramas_command,
        filters.command("s", prefixes="/")
    )
)


# -------------------------------------------------------------------
# Handler: Drama Details Callback
# -------------------------------------------------------------------
app.add_handler(
    CallbackQueryHandler(
        drama_details_callback,
        filters.regex("^details")
    )
)


# -------------------------------------------------------------------
# Handler: /url
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        handle_drama_url,
        filters.command("url", prefixes="/")
    )
)


# -------------------------------------------------------------------
# Handler: Close Search Results (Callback)
# -------------------------------------------------------------------
app.add_handler(
    CallbackQueryHandler(
        close_search_results,
        filters.regex("^close_search")
    )
)


# -------------------------------------------------------------------
# Handler: /settemplate (User-specific template)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        set_template_command,
        filters.command("settemplate", prefixes="/")
    )
)

# -------------------------------------------------------------------
# Handler: /gettemplate (User-specific template)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        get_template_command,
        filters.command("gettemplate", prefixes="/")
    )
)

# -------------------------------------------------------------------
# Handler: /removetemplate (User-specific template)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        remove_template_command,
        filters.command("removetemplate", prefixes="/")
    )
)

# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Handler: /previewtemplate (User-specific template)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        preview_template_command,
        filters.command("previewtemplate", prefixes="/")
    )
)

# -------------------------------------------------------------------
# Handler: /log (Owner only)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        send_log,
        filters.command("log", prefixes="/") & filters.user(OWNER_ID)
    )
)

# -------------------------------------------------------------------
# Handler: /help    
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        help_command,
        filters.command("help", prefixes="/")
    )
)

# -------------------------------------------------------------------
# Handler: /userstats (Owner only)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        user_stats_command,
        filters.command("userstats", prefixes="/") & filters.user(OWNER_ID)
    )
)

# -------------------------------------------------------------------
# Handler: /publicmode (Owner only)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        set_public_mode_command,
        filters.command("setpublicmode", prefixes="/") & filters.user(OWNER_ID)
    )
)

# -------------------------------------------------------------------
# Handler: /broadcast (Owner only)
# -------------------------------------------------------------------
app.add_handler(
    MessageHandler(
        manual_broadcast_command,
        filters.command("broadcast", prefixes="/") & filters.user(OWNER_ID)
    )
)

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        # Pass the function itself (no parentheses):
        app.run()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
