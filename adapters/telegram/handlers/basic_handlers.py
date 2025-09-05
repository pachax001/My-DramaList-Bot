"""Basic bot command handlers."""

import os
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from infra.config import settings
from infra.logging import get_logger
from infra.db import mongo_client

logger = get_logger(__name__)


async def start_command(client: Client, message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()

    logger.info(f"User {user_id} ({username}) started the bot")

    # Update user info in database
    await mongo_client.db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "username": username,
                "full_name": full_name,
                "last_active": message.date
            }
        },
        upsert=True
    )

    if user_id == settings.owner_id:
        # Owner gets admin info
        total_users = await mongo_client.db.users.count_documents({})
        
        # Get public mode status
        public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
        is_public = public_setting.get("value", False) if public_setting else settings.is_public
        
        text = (
            f"👋 Hello, Owner (ID: `{settings.owner_id}`).\n\n"
            f"🔓 **Bot Public Mode:** {'Enabled' if is_public else 'Disabled'}\n\n"
            f"👥 **Total Users:** {total_users}\n\n"
            "⚙️ Use the following commands to manage access:\n"
            "/authorize <user_id> - Grant access\n"
            "/unauthorize <user_id> - Revoke access\n\n"
            "📄 Use /help to see all available commands."
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💻 Source Code", url="https://github.com/pachax001/My-DramaList-Bot")],
            [InlineKeyboardButton("Search Inline (MyDramaList)", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")]
        ])
        
    else:
        # Regular users
        text = (
            f"👋 Welcome to MyDramaList Bot!\n\n"
            "🎭 **Available Commands:**\n"
            "/mdl <query> - Search MyDramaList\n"
            "/imdb <query> - Search IMDB\n"
            "/mdlurl <url> - Get drama by URL\n"
            "/imdburl <url> - Get movie by URL\n\n"
            "🎨 **Template Commands:**\n"
            "/setmdltemplate - Set custom MDL template\n"
            "/setimdbtemplate - Set custom IMDB template\n\n"
            "Use /help for more detailed information!"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Search Inline (MyDramaList)", switch_inline_query_current_chat="")]
        ])

    await message.reply_text(text, reply_markup=keyboard)


async def help_command(client: Client, message: Message):
    """Handle /help command."""
    help_text = """
🎭 **MyDramaList & IMDB Telegram Bot**

**🔍 Search Commands:**
/mdl <query> - Search dramas on MyDramaList
/imdb <query> - Search movies/shows on IMDB
/mdlurl <url> - Get drama details by MyDramaList URL
/imdburl <url> - Get movie details by IMDB URL

**🎨 Template Commands:**
/setmdltemplate <template> - Set custom MyDramaList template
/getmdltemplate - View your current MDL template
/removemdltemplate - Remove your MDL template
/previewmdltemplate - Preview your MDL template

/setimdbtemplate <template> - Set custom IMDB template
/getimdbtemplate - View your current IMDB template
/removeimdbtemplate - Remove your IMDB template
/previewimdbtemplate - Preview your IMDB template

**📱 Inline Search:**
Type `@botusername <query>` in any chat to search MyDramaList inline

**👑 Owner Commands:**
/authorize <user_id> - Grant bot access
/unauthorize <user_id> - Remove bot access
/users - View authorized users
/userstats - Get user statistics
/setpublicmode <on/off> - Toggle public mode
/broadcast <message> - Send message to all users
/log - Get bot logs
/health - Check service health

**💡 Template Variables:**

**MyDramaList:** {title}, {rating}, {synopsis}, {country}, {episodes}, {genres}, etc.

**IMDB:** {title}, {year}, {rating}, {plot}, {cast}, {director}, {genres}, etc.

Example template:
`<b>{title}</b> ({year})
Rating: {rating} ⭐️
{plot}`

Need help? Contact: @matthewmurdockbot
"""
    
    await message.reply_text(help_text)


async def send_log(client: Client, message: Message):
    """Send bot log file to owner."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can access logs.")
    
    try:
        # Check if log file exists
        log_files = ["bot.log", "app.log", "main.log"]
        log_file = None
        
        for filename in log_files:
            if os.path.exists(filename):
                log_file = filename
                break
        
        if log_file and os.path.getsize(log_file) > 0:
            await message.reply_document(log_file, caption="📄 Bot Log File")
        else:
            await message.reply_text("📄 No log file available or file is empty.")
            
    except Exception as e:
        logger.error(f"Error sending log: {e}")
        await message.reply_text("❌ Failed to send log file.")


async def user_stats_command(client: Client, message: Message):
    """Get user statistics."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can view statistics.")
    
    try:
        # Get user statistics
        total_users = await mongo_client.db.users.count_documents({})
        authorized_users = await mongo_client.db.authorized_users.count_documents({})
        
        # Get template usage
        mdl_templates = await mongo_client.db.mdl_templates.count_documents({})
        imdb_templates = await mongo_client.db.imdb_templates.count_documents({})
        
        # Get public mode status
        public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
        is_public = public_setting.get("value", False) if public_setting else settings.is_public
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Users:**
• Total Users: {total_users}
• Authorized Users: {authorized_users}

🎨 **Templates:**
• MDL Templates: {mdl_templates}
• IMDB Templates: {imdb_templates}

⚙️ **Settings:**
• Public Mode: {'Enabled' if is_public else 'Disabled'}

🔧 **System:**
• Redis Caching: Enabled
• MongoDB: Connected
• HTTP Pooling: Active
"""
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        await message.reply_text("❌ Failed to get user statistics.")


async def set_public_mode_command(client: Client, message: Message):
    """Toggle public mode on/off."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can change public mode.")
    
    parts = message.text.split()
    if len(parts) != 2 or parts[1].lower() not in ['on', 'off']:
        return await message.reply_text("Usage: /setpublicmode <on/off>")
    
    try:
        new_mode = parts[1].lower() == 'on'
        
        # Update in database
        await mongo_client.db.settings.update_one(
            {"key": "public_mode"},
            {"$set": {"value": new_mode}},
            upsert=True
        )
        
        mode_text = "enabled" if new_mode else "disabled"
        logger.info(f"Public mode {mode_text} by owner {settings.owner_id}")
        
        await message.reply_text(f"✅ Public mode has been **{mode_text}**.")
        
    except Exception as e:
        logger.error(f"Error setting public mode: {e}")
        await message.reply_text("❌ Failed to update public mode.")


async def manual_broadcast_command(client: Client, message: Message):
    """Broadcast message to all users."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can broadcast messages.")
    
    # Get broadcast content
    if message.reply_to_message:
        broadcast_content = {
            'media_type': 'text',
            'text': message.reply_to_message.text or message.reply_to_message.caption or "No content",
        }
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            return await message.reply_text("Usage: /broadcast <message> or reply to a message")
        
        broadcast_content = {
            'media_type': 'text', 
            'text': parts[1]
        }
    
    try:
        # Get all users
        users = []
        async for user in mongo_client.db.users.find():
            users.append(user['user_id'])
        
        if not users:
            return await message.reply_text("❌ No users to broadcast to.")
        
        # Start broadcast
        broadcast_msg = await message.reply_text(f"📢 Starting broadcast to {len(users)} users...")
        
        # Simple broadcast (replace with proper broadcast logic from old code)
        sent = 0
        failed = 0
        
        for user_id in users:
            try:
                await client.send_message(user_id, broadcast_content['text'])
                sent += 1
            except Exception:
                failed += 1
        
        await broadcast_msg.edit_text(f"✅ Broadcast completed!\n📤 Sent: {sent}\n❌ Failed: {failed}")
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        await message.reply_text("❌ Broadcast failed.")