import asyncio
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, FORCE_SUB_CHANNEL_URL
from bot.permissions.use_bot import user_can_use_bot, is_subscribed
import os
from bot.db.user_db import add_or_update_user,get_total_users,get_recent_users, get_all_template_counts, get_template_count, get_imdb_template_count
from bot.logger.logger import logger
from bot.db.config_db import set_public_mode,get_public_mode
from bot.helper.user_management.broadcast import broadcast_to_users
from pyrogram.enums import  ParseMode
OWNER_PROFILE_URL = "https://t.me/matthewmurdockbot"
SOURCE_CODE_URL = "https://github.com/pachax001/My-DramaList-Bot"
#ADULT_CONTENT_CHANNEL = "https://t.me/eseoaOF"
channel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Main Channel", url=FORCE_SUB_CHANNEL_URL)]])
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()

    logger.info(f"User {user_id} ({username}) started the bot.")
    if get_public_mode():
        add_or_update_user(user_id, username, full_name)
        logger.info(f"User {user_id} activity updated in the database.")
    

    if user_id == OWNER_ID:
        total_users = get_total_users()
        text = (
            f"👋 Hello, Owner (ID: <code>{OWNER_ID}</code>).\n\n"
            f"🔓 <b>Bot Public Mode:</b> {'Enabled' if get_public_mode() else 'Disabled'}\n\n"
            f"👥 <b>Total Users:</b> {total_users}\n\n"
            "⚙️ Use the following commands to manage access:\n"
            "/authorize <user_id> - Grant access\n"
            "/unauthorize <user_id> - Revoke access\n\n"
            "📄 Use /help to see all available commands."
        )
        keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💻 Source Code", url=SOURCE_CODE_URL)],
        [InlineKeyboardButton("Search Inline (Only MyDramalist)", switch_inline_query_current_chat="")],
        #[InlineKeyboardButton("🔞 Adult Content Channel", url=ADULT_CONTENT_CHANNEL)],
        [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")],
    ])
    else:
        if await user_can_use_bot(user_id):
            if not await is_subscribed(client,user_id):
                return await message.reply_text(
                    text="You have not subscribed to my channel.. Subscribe and send /start again",
                    reply_markup=channel_markup)
            else:
                text = (
                    f"👋 Hello <b>{username}</b>!\n\n"
                    "✅ You have access to this bot.\n"
                    "Use the commands below to get started:\n\n"
                    "🔍 <b>Search Dramas on Mydramalist:</b> <code>/mdl &lt;query&gt;</code>\n"
                    "🔍 <b>Search on IMDB:</b> <code>/imdb &lt;query&gt;</code>\n"
                    "🔗 <b>Get Details by Mydramalist URL:</b> <code>/mdlurl &lt;mydramalistURL&gt; or reply to URL</code>\n"
                    "🔗 <b>Get Details by IMDB URL:</b> <code>/imdburl &lt;imdbURL&gt; or reply to URL</code>\n\n"
                    "📄 Use /help to explore all available commands.\n"
                    "❗This is not a content giving or file giving bot. This just gives you the details of the movie or drama. It does not provide any files or content. Use at your own risk.\n"
                    "📁For getting files use @filefilter001bot or @filefilter0012bot"
                )

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Search Inline (Only MyDramalist)", switch_inline_query_current_chat="")],
                    [InlineKeyboardButton("Help", callback_data="help_command")],
                    [InlineKeyboardButton("K-Drama Channel", url=FORCE_SUB_CHANNEL_URL)],
                    #[InlineKeyboardButton("🔞 Adult Content Channel", url=ADULT_CONTENT_CHANNEL)],
                    [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")],

                ])
        else:
            text = (
                "❌ <b>Access Denied</b>\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the bot owner for access."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Contact Owner", url=OWNER_PROFILE_URL)],
                [InlineKeyboardButton("K-Drama Channel", url=FORCE_SUB_CHANNEL_URL)],
                #[InlineKeyboardButton("🔞 Adult Content Channel", url=ADULT_CONTENT_CHANNEL)],
                [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")],
            ])
    return await message.reply_text(text, reply_markup=keyboard)



async def send_log(client: Client, message: Message):
    if os.path.exists("log.txt"):
        await message.reply_document(document="log.txt")
    else:
        await message.reply_text("Log file not found.")



async def help_command(client: Client, message: Message):
    """Handles the /help command and provides guidance to users."""
    if await user_can_use_bot(message.from_user.id):
        if not await is_subscribed(client,message.from_user.id):
            return await message.reply_text(
                text="You have not subscribed to my channel.. Subscribe and send /start again",
                reply_markup=channel_markup)
        else:
            help_text = (
                "**Bot Commands:**\n\n"
                
                "📖 **General Commands:**\n"
                "`/start` - Start the bot and get a welcome message\n"
                "`/help` - Show this help message\n"
                 "**MyDramalist Commands:**\n\n"
                "`/mdl &lt;query&gt;` - Search for a drama by title\n"
                "`/mdlurl &lt;mydramalistURL&gt;` - Get drama details by URL (Replying to the URL also works)\n\n"
    
                "⚙️ **User Commands MyDramalist:**\n"
                "`/setmdltemplate &lt;template&gt;` - Set a custom display template for MyDramalist Results\n"
                "`/getmdltemplate` - View your current MyDramalist template\n"
                "`/removemdltemplate` - Remove your custom MyDramalist template\n"
                "`/previewmdltemplate` - Preview your custom MyDramalist template\n\n"
    
                "🔍 **Inline Query Usage (Only works for MyDramalist):**\n"
                "Simply type `@mydramalist001bot` followed by your search query in any chat. Only works for MyDramalist\n"
                "Example:\n"
                "`@mydramalist001bot Vincenzo`\n\n"
                 "**IMDB Commands:**\n\n"
                "`/imdb &lt;query&gt;` - Search on IMDB using a keyword\n"
                "`/imdburl &lt;IMDBURL&gt;` - Get details by URL (Replying to the URL also works)\n\n"
                
                "⚙️ **User Commands IMDB:**\n"
                "`/setimdbtemplate <template>` - Set a custom display template for IMDB Results\n"
                "`/getimdbtemplate` - View your current IMDB template\n"
                "`/removeimdbtemplate` - Remove your custom IMDB template\n"
                "`/previewimdbtemplate` - Preview your custom IMDB template\n\n"
    
                "🔐 **Admin Commands:**\n"
                "`/authorize <user_id>` - Allow a user to access the bot\n"
                "`/unauthorize <user_id>` - Remove access from a user\n"
                "`/users` - View authorized users\n"
                "`/log` - Retrieve the bot's log file\n\n"
    
                "For more details, contact the bot owner."
            )

            # Inline keyboard with buttons to owner profile and source code
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Owner", url=OWNER_PROFILE_URL)],
                [InlineKeyboardButton("💻 Source Code", url=SOURCE_CODE_URL)],
                [InlineKeyboardButton("K-Drama Channel", url=FORCE_SUB_CHANNEL_URL)],
                #[InlineKeyboardButton("🔞 Adult Content Channel", url=ADULT_CONTENT_CHANNEL)],
                [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")],

            ])

            return await message.reply_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

    else:
        return await message.reply_text("You are not authorized to use this bot.")



async def user_stats_command(client: Client, message: Message):
    """Allows the owner to check user statistics."""
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("You are not authorized to view this information.")

    total_users = get_total_users()
    recent_users = get_recent_users(days=7)
    total_templates = get_all_template_counts()
    total_mdl_templates = get_template_count()
    total_imdb_templates = get_imdb_template_count()
    stats_text = (
        f"📊 <b>User Statistics:</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📅 Active in Last 7 Days: <b>{recent_users}</b>\n"
        f"📃 Total Templates: <b>{total_templates}</b>\n"
        f"🍿 Total MDL Templates: <b>{total_mdl_templates}</b>\n"
        f"📽️ Total IMD Templates: <b>{total_imdb_templates}</b>\n\n"
        "Use /help to see available commands."
    )

    return await message.reply_text(stats_text)



async def set_public_mode_command(client: Client, message: Message):
    """Command to toggle public mode on or off and notify users."""
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this command.")

    parts = message.text.split(" ", 1)
    if len(parts) < 2 or parts[1].lower() not in ["on", "off"]:
        return await message.reply_text("⚙️ Usage: /setpublicmode on|off")

    new_status = parts[1].lower() == "on"
    current_status = get_public_mode()

    if new_status == current_status:
        return await message.reply_text(f"⚠️ Public mode is already {'enabled' if new_status else 'disabled'}.")

    # Update public mode in the database
    set_public_mode(new_status)
    status_text = "Enabled ✅" if new_status else "Disabled ❌"
    await message.reply_text(f"✅ Public Mode has been <b>{status_text}</b>")

    # Notify users about the mode change
    broadcast_message = (
        "📢 <b>Notice:</b>\n\n"
        "🚀 The bot is now available to all users. You can start searching dramas!" if new_status
        else "🔒 <b>Notice:</b>\n\n"
             "The bot is now in private mode. Only authorized users can access it."
    )

    return await broadcast_to_users(client, broadcast_message, batch_size=30, delay=2)



# async def manual_broadcast_command(client: Client, message: Message):
#     """Broadcast custom messages to all users."""
#     if message.from_user.id != OWNER_ID:
#         return await message.reply_text("❌ You are not authorized to use this command.")
#
#     if message.reply_to_message:
#         custom_message = message.reply_to_message.text or message.reply_to_message.caption
#         if not custom_message:
#             return await message.reply_text("⚙️ The replied message does not contain any text to broadcast.")
#
#     else:
#         parts = message.text.split(" ", 1)
#         if len(parts) < 2:
#             return await message.reply_text("⚙️ Usage: /broadcast message")
#         custom_message = parts[1]
#     await broadcast_to_users(client, custom_message)
#     return await message.reply_text("✅ Message has been broadcasted successfully.")

async def manual_broadcast_command(client: Client, message: Message):
    """Handle media broadcast commands"""
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Unauthorized")

    content = {'media_type': 'text'}

    if message.reply_to_message:
        msg = message.reply_to_message
        content['caption'] = msg.caption or ""
        #content['parse_mode'] = ParseMode.HTML

        if msg.text:
            content.update({
                'media_type': 'text',
                'text': msg.text
            })
        elif msg.photo:
            content.update({
                'media_type': 'photo',
                'media_file': msg.photo.file_id
            })
        elif msg.video:
            content.update({
                'media_type': 'video',
                'media_file': msg.video.file_id
            })
        elif msg.document:
            content.update({
                'media_type': 'document',
                'media_file': msg.document.file_id
            })
        else:
            return await message.reply_text("❌ Unsupported media type")
    else:
        text = message.text.split(" ", 1)
        if len(text) < 2:
            return await message.reply_text("⚙️ Usage: /broadcast (message or reply to media)")
        content.update({
            'text': text[1],
            'media_type': 'text'
        })
    broadcast_message = await message.reply_text(f"✅ Broadcast started! Media type: {content['media_type']}")
    await asyncio.sleep(2)
    return await broadcast_to_users(client, content,broadcast_message)


