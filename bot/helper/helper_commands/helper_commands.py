from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from bot.permissions.use_bot import user_can_use_bot
import os
from bot.db.user_db import add_or_update_user,get_total_users,get_recent_users
from bot.logger.logger import logger
from datetime import timedelta
from bot.db.config_db import set_public_mode,get_public_mode
from bot.helper.user_management.broadcast import broadcast_to_users
from pyrogram.enums import ParseMode
OWNER_PROFILE_URL = "https://t.me/gunaya001"
SOURCE_CODE_URL = "https://github.com/YourGitHubRepo"
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
        [InlineKeyboardButton("Search Inline", switch_inline_query_current_chat="")]
    ])
    else:
        if user_can_use_bot(user_id):
            text = (
                f"👋 Hello <b>{username}</b>!\n\n"
                "✅ You have access to this bot.\n"
                "Use the commands below to get started:\n\n"
                "🔍 <b>Search Dramas:</b> <code>/s &lt;query&gt;</code>\n"
                "🔗 <b>Get Details by URL:</b> <code>/url &lt;mydramalistURL&gt;</code>\n\n"
                "📄 Use /help to explore all available commands."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Search Inline", switch_inline_query_current_chat="")],
                [InlineKeyboardButton("Help", callback_data="help_command")]
            ])
        else:
            text = (
                "❌ <b>Access Denied</b>\n\n"
                "You are not authorized to use this bot.\n"
                "Please contact the bot owner for access."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Contact Owner", url="https://t.me/YourOwnerUsername")]
            ])

    await message.reply_text(text, reply_markup=keyboard)



async def send_log(client: Client, message: Message):
    if os.path.exists("log.txt"):
        await message.reply_document(document="log.txt")
    else:
        await message.reply_text("Log file not found.")



async def help_command(client: Client, message: Message):
    """Handles the /help command and provides guidance to users."""
    if user_can_use_bot(message.from_user.id) or message.from_user.id == OWNER_ID:
        help_text = (
            "**MyDramaList Bot Commands:**\n\n"
            
            "📖 **General Commands:**\n"
            "`/start` - Start the bot and get a welcome message\n"
            "`/help` - Show this help message\n"
            "`/s <query>` - Search for a drama by title\n"
            "`/url <mydramalist_url>` - Get drama details by URL\n\n"

            "⚙️ **User Commands:**\n"
            "`/settemplate <template>` - Set a custom display template\n"
            "`/gettemplate` - View your current template\n"
            "`/removetemplate` - Remove your custom template\n"
            "`/previewtemplate` - Preview your custom template\n\n"

            "🛠 **Template Setting Guide:**\n"
            "**Usage:** `/settemplate Your Template`\n\n"
            "**Available placeholders:**\n\n"
            "**➤ Drama Info**\n"
            "`{title}`, `{complete_title}`, `{link}`, `{rating}`, `{synopsis}`\n\n"
            "**➤ Details**\n"
            "`{country}`, `{type}`, `{episodes}`, `{aired}`, `{aired_on}`, `{original_network}`\n\n"
            "**➤ Additional Info**\n"
            "`{duration}`, `{content_rating}`, `{score}`, `{ranked}`, `{popularity}`,\n"
            "`{watchers}`, `{favorites}`, `{genres}`, `{tags}`, `{native_title}`, `{also_known_as}`\n\n"
            "**HTML Formatting Supported:**\n"
            "`<b>Bold</b>`, `<strong>Strong</strong>`, `<i>Italic</i>`, `<em>Emphasis</em>`, `<u>Underline</u>`,\n"
            "`<ins>Inserted</ins>`, `<s>Strikethrough</s>`, `<strike>Strike</strike>`, `<del>Deleted</del>`,\n"
            "`<code>Code</code>`, `<pre>Preformatted</pre>`, `<a href='https://mydramalist.com/'>Link</a>`\n\n"

            "🔍 **Inline Query Usage:**\n"
            "Simply type `@mydramalist001bot` followed by your search query in any chat.\n"
            "Example:\n"
            "`@mydramalist001bot Vincenzo`\n\n"

            "🔐 **Admin Commands:**\n"
            "`/authorize <user_id>` - Allow a user to access the bot\n"
            "`/unauthorize <user_id>` - Remove access from a user\n"
            "`/users` - View authorized users\n"
            "`/log` - Retrieve the bot's log file\n\n"

            "💡 **Usage Examples:**\n"
            "`/s Vincenzo`\n"
            "`/url https://mydramalist.com/12345-vincenzo`\n"
            "`/settemplate <b>{title}</b> - {rating}⭐ | {episodes} Episodes`\n\n"

            "For more details, contact the bot owner."
        )

        # Inline keyboard with buttons to owner profile and source code
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Owner", url=OWNER_PROFILE_URL)],
            [InlineKeyboardButton("💻 Source Code", url=SOURCE_CODE_URL)]
        ])

        await message.reply_text(help_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("You are not authorized to use this bot.")



async def user_stats_command(client: Client, message: Message):
    """Allows the owner to check user statistics."""
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("You are not authorized to view this information.")

    total_users = get_total_users()
    recent_users = get_recent_users(days=7)

    stats_text = (
        f"📊 <b>User Statistics:</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"📅 Active in Last 7 Days: <b>{recent_users}</b>\n\n"
        "Use /help to see available commands."
    )

    await message.reply_text(stats_text)

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

    await broadcast_to_users(client, broadcast_message, batch_size=30, delay=2)


async def manual_broadcast_command(client: Client, message: Message):
    """Broadcast custom messages to all users."""
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ You are not authorized to use this command.")

    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return await message.reply_text("⚙️ Usage: /broadcast message")

    custom_message = parts[1]
    await broadcast_to_users(client, custom_message)
    await message.reply_text("✅ Message has been broadcasted successfully.")
