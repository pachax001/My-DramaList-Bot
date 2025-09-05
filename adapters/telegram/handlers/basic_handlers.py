"""Basic bot command handlers."""

import os
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
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
            f"👋 Hello, Owner (ID: <code>{settings.owner_id}</code>).\n\n"
            f"🔓 <b>Bot Public Mode:</b> {'Enabled' if is_public else 'Disabled'}\n\n"
            f"👥 <b>Total Users:</b> {total_users}\n\n"
            "⚙️ Use the following commands to manage access:\n"
            "/authorize &lt;user_id&gt; - Grant access\n"
            "/unauthorize &lt;user_id&gt; - Revoke access\n\n"
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

    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def help_command(client: Client, message: Message):
    """Handle /help command."""
    help_text = """
🎭 **MyDramaList & IMDB Telegram Bot**

**🔍 Search Commands:**
/mdl <query> - Search dramas on MyDramaList
/mdl <url> - Process MyDramaList URL directly
/imdb <query> - Search movies/shows on IMDB
/imdb <url> - Process IMDB URL directly
/mdlurl <url> - Get drama details by URL
/imdburl <url> - Get movie/show details by URL

*You can also reply to messages containing URLs with these commands!*

**🎨 Template Commands:**
/setmdltemplate <template> - Set custom MyDramaList template
/getmdltemplate - View your current MDL template
/removemdltemplate - Remove your MDL template
/previewmdltemplate - Preview your MDL template
/mdlplaceholders - Show all MyDramaList placeholders

/setimdbtemplate <template> - Set custom IMDB template
/getimdbtemplate - View your current IMDB template
/removeimdbtemplate - Remove your IMDB template
/previewimdbtemplate - Preview your IMDB template
/imdbplaceholders - Show all IMDB placeholders

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
/cachereload - Clear all caches and restart cache client

**💡 Template Guide:**

**Basic Example:**
```
<b>{title}</b> ({year})
Rating: {rating} ⭐️
{plot}
```

**MyDramaList Sample:**
```
🎭 <b>{title}</b>
📍 Country: {country} | Episodes: {episodes}
⭐ Rating: {rating}
🎬 Genres: {genres}
📖 {synopsis}
```

**IMDB Sample:**
```
🎬 <b>{title}</b> ({year})
⭐ {rating}/10 ({votes} votes)
🎭 Cast: {cast}
🎬 Directors: {directors}
📝 {plot}
```

Use /mdlplaceholders or /imdbplaceholders to see all available fields!

Need help? Contact: @matthewmurdockbot
"""
    
    await message.reply_text(help_text)


async def send_log(client: Client, message: Message):
    """Send bot log file to owner."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can access logs.")
        return
    
    try:
        import glob
        
        # Look for log files in various locations
        log_patterns = [
            "logs/current.log",    # Current log symlink
            "logs/bot_*.log",      # Docker/container logs  
            "bot*.log",            # Current directory logs
            "app.log",             # Standard app log
            "main.log"             # Main log file
        ]
        
        log_file = None
        latest_time = 0
        
        # Find the most recent log file
        for pattern in log_patterns:
            files = glob.glob(pattern)
            for file_path in files:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    file_time = os.path.getmtime(file_path)
                    if file_time > latest_time:
                        latest_time = file_time
                        log_file = file_path
        
        if log_file:
            # Send only the last 50 lines if file is too large
            file_size = os.path.getsize(log_file)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await message.reply_text("📄 Log file is too large. Sending last 1000 lines...")
                
                # Read last 1000 lines
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = ''.join(lines[-1000:]) if len(lines) > 1000 else ''.join(lines)
                
                # Create temporary file with recent logs
                temp_log = "recent_logs.txt"
                with open(temp_log, 'w', encoding='utf-8') as f:
                    f.write(last_lines)
                
                await message.reply_document(temp_log, caption=f"📄 Recent Bot Logs (last 1000 lines)\nFrom: {log_file}")
                os.remove(temp_log)  # Clean up temp file
            else:
                await message.reply_document(log_file, caption=f"📄 Bot Log File\nFrom: {log_file}")
        else:
            await message.reply_text("📄 No log file available or all files are empty.")
            
    except Exception as e:
        logger.error(f"Error sending log: {e}")
        await message.reply_text("❌ Failed to send log file.")


async def user_stats_command(client: Client, message: Message):
    """Get user statistics."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can view statistics.")
        return
    
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
📊 <b>Bot Statistics</b>

👥 <b>Users:</b>
• Total Users: {total_users}
• Authorized Users: {authorized_users}

🎨 <b>Templates:</b>
• MDL Templates: {mdl_templates}
• IMDB Templates: {imdb_templates}

⚙️ <b>Settings:</b>
• Public Mode: {'Enabled' if is_public else 'Disabled'}

🔧 <b>System:</b>
• Redis Caching: Enabled
• MongoDB: Connected
• HTTP Pooling: Active
"""
        
        await message.reply_text(stats_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        await message.reply_text("❌ Failed to get user statistics.")


async def set_public_mode_command(client: Client, message: Message):
    """Toggle public mode on/off."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can change public mode.")
        return
    
    parts = message.text.split()
    if len(parts) != 2 or parts[1].lower() not in ['on', 'off']:
        await message.reply_text("Usage: /setpublicmode <on/off>")
        return
    
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
        
        # Update bot commands to reflect new mode
        try:
            from app.commands import BotCommandManager
            await BotCommandManager.update_commands_for_mode_change(client, settings.owner_id, new_mode)
            command_status = "Bot commands updated automatically."
        except Exception as cmd_error:
            logger.error(f"Failed to update bot commands: {cmd_error}")
            command_status = "⚠️ Bot commands may need manual restart to update."
        
        await message.reply_text(f"✅ Public mode has been **{mode_text}**.\n{command_status}")
        
    except Exception as e:
        logger.error(f"Error setting public mode: {e}")
        await message.reply_text("❌ Failed to update public mode.")


async def cache_reload_command(client: Client, message: Message):
    """Hot reload cache - clear all caches and restart cache client."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can reload caches.")
        return
    
    try:
        from infra.cache import cache_client
        from infra.ratelimit.limiter import api_limiter, user_limiter, global_limiter
        
        # Clear all cache namespaces
        cache_stats = {}
        if cache_client._redis:
            # Get cache info before clearing
            info = await cache_client._redis.info('memory')
            cache_stats['before_memory'] = info.get('used_memory_human', 'Unknown')
            
            # Clear all keys with our namespace prefixes
            namespaces = ['v1:imdb_search:*', 'v1:imdb_details:*', 'v1:mdl_search:*', 
                         'v1:mdl_details:*', 'v1:user_templates:*', 'ratelimit:*']
            
            cleared_count = 0
            for pattern in namespaces:
                keys = await cache_client._redis.keys(pattern)
                if keys:
                    cleared_count += await cache_client._redis.delete(*keys)
            
            cache_stats['cleared_keys'] = cleared_count
            
            # Get memory info after clearing
            info = await cache_client._redis.info('memory')
            cache_stats['after_memory'] = info.get('used_memory_human', 'Unknown')
        else:
            # Clear local rate limiter buckets
            api_limiter._local_buckets.clear()
            user_limiter._local_buckets.clear()
            global_limiter._local_buckets.clear()
            cache_stats['local_buckets_cleared'] = True
        
        # Restart Redis connection
        await cache_client.close()
        await cache_client.start()
        
        connection_status = "✅ Connected" if cache_client._redis else "⚠️ Unavailable (local fallback)"
        
        stats_text = f"""
🔄 <b>Cache Reload Complete</b>

🗄️ <b>Redis Status:</b> {connection_status}
"""
        
        if 'cleared_keys' in cache_stats:
            stats_text += f"""
📊 <b>Cleared Data:</b>
• Keys cleared: {cache_stats['cleared_keys']}
• Memory before: {cache_stats['before_memory']}
• Memory after: {cache_stats['after_memory']}
"""
        elif 'local_buckets_cleared' in cache_stats:
            stats_text += """
📊 <b>Cleared Data:</b>
• Local rate limit buckets cleared
• Redis unavailable, using local fallback
"""
        
        logger.info(f"Cache reload completed by owner {settings.owner_id}")
        await message.reply_text(stats_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error reloading cache: {e}")
        await message.reply_text(f"❌ Cache reload failed: {str(e)}")


async def manual_broadcast_command(client: Client, message: Message):
    """Broadcast message to all users."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can broadcast messages.")
        return
    
    # Get broadcast content
    if message.reply_to_message:
        broadcast_content = {
            'media_type': 'text',
            'text': message.reply_to_message.text or message.reply_to_message.caption or "No content",
        }
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text("Usage: /broadcast <message> or reply to a message")
            return
        
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
            await message.reply_text("❌ No users to broadcast to.")
            return
        
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