"""Basic bot command handlers."""

import os
import sys
import asyncio
import subprocess
import json
import re
from datetime import datetime
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
            [InlineKeyboardButton("🍺 Buy Me A Beer", url="https://buymeacoffee.com/matthewmurdock001")]
        ])
        
    else:
        # Regular users
        text = (
            f"👋 Welcome to MyDramaList Bot!\n\n"
            "🎭 <b>Available Commands:</b>\n"
            "/mdl &lt;query&gt; - Search MyDramaList\n"
            "/imdb &lt;query&gt; - Search IMDB\n"
            "/mdlurl &lt;url&gt; - Get drama by URL\n"
            "/imdburl &lt;url&gt; - Get movie by URL\n\n"
            "🎨 <b>Template Commands:</b>\n"
            "/setmdltemplate - Set custom MDL template\n"
            "/setimdbtemplate - Set custom IMDB template\n\n"
            "Use /help for more detailed information!"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💻 Source Code", url="https://github.com/pachax001/My-DramaList-Bot")]
        ])

    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def help_command(client: Client, message: Message):
    """Handle /help command."""
    help_text = """
🎭 <b>MyDramaList & IMDB Telegram Bot</b>

<b>🔍 Search Commands:</b>
/mdl &lt;query&gt; - Search dramas on MyDramaList
/mdl &lt;url&gt; - Process MyDramaList URL directly
/imdb &lt;query&gt; - Search movies/shows on IMDB
/imdb &lt;url&gt; - Process IMDB URL directly
/mdlurl &lt;url&gt; - Get drama details by URL
/imdburl &lt;url&gt; - Get movie/show details by URL

<i>You can also reply to messages containing URLs with these commands!</i>

<b>🎨 Template Commands:</b>
/setmdltemplate &lt;template&gt; - Set custom MyDramaList template
/getmdltemplate - View your current MDL template
/removemdltemplate - Remove your MDL template
/previewmdltemplate - Preview your MDL template
/mdlplaceholders - Show all MyDramaList placeholders

/setimdbtemplate &lt;template&gt; - Set custom IMDB template
/getimdbtemplate - View your current IMDB template
/removeimdbtemplate - Remove your IMDB template
/previewimdbtemplate - Preview your IMDB template
/imdbplaceholders - Show all IMDB placeholders


<b>👑 Owner Commands:</b>
/authorize &lt;user_id&gt; - Grant bot access
/unauthorize &lt;user_id&gt; - Remove bot access
/users - View authorized users
/userstats - Get user statistics
/setpublicmode &lt;on/off&gt; - Toggle public mode
/broadcast &lt;message&gt; - Send message to all users
/log - Get bot logs
/health - Check service health
/cachereload - Clear all caches and restart cache client

<b>💡 Template Guide:</b>

<b>Basic Example:</b>
<pre>
&lt;b&gt;{title}&lt;/b&gt; ({year})
Rating: {rating} ⭐️
{plot}
</pre>

<b>MyDramaList Sample:</b>
<pre>
🎭 &lt;b&gt;{title}&lt;/b&gt;
📍 Country: {country} | Episodes: {episodes}
⭐ Rating: {rating}
🎬 Genres: {genres}
📖 {synopsis}
</pre>

<b>IMDB Sample:</b>
<pre>
🎬 &lt;b&gt;{title}&lt;/b&gt; ({year})
⭐ {rating}/10 ({votes} votes)
🎭 Cast: {cast}
🎬 Directors: {directors}
📝 {plot}
</pre>

Use /mdlplaceholders or /imdbplaceholders to see all available fields!

Need help? Contact: @matthewmurdockbot
"""
    
    await message.reply_text(help_text, parse_mode=ParseMode.HTML)


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
        
        await message.reply_text(f"✅ Public mode has been <b>{mode_text}</b>.\n{command_status}", parse_mode=ParseMode.HTML)
        
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
    """Enhanced broadcast supporting all message types with batch processing for millions of users."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can broadcast messages.")
        return
    
    # Get broadcast content
    broadcast_content = {}
    
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        
        # Handle different message types
        if replied_msg.photo:
            broadcast_content = {
                'type': 'photo',
                'media': replied_msg.photo.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.video:
            broadcast_content = {
                'type': 'video',
                'media': replied_msg.video.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.animation:
            broadcast_content = {
                'type': 'animation',
                'media': replied_msg.animation.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.document:
            broadcast_content = {
                'type': 'document',
                'media': replied_msg.document.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.audio:
            broadcast_content = {
                'type': 'audio',
                'media': replied_msg.audio.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.voice:
            broadcast_content = {
                'type': 'voice',
                'media': replied_msg.voice.file_id,
                'caption': replied_msg.caption or "",
                'parse_mode': ParseMode.HTML
            }
        elif replied_msg.video_note:
            broadcast_content = {
                'type': 'video_note',
                'media': replied_msg.video_note.file_id,
            }
        elif replied_msg.sticker:
            broadcast_content = {
                'type': 'sticker',
                'media': replied_msg.sticker.file_id,
            }
        elif replied_msg.location:
            broadcast_content = {
                'type': 'location',
                'latitude': replied_msg.location.latitude,
                'longitude': replied_msg.location.longitude,
            }
        elif replied_msg.contact:
            broadcast_content = {
                'type': 'contact',
                'phone_number': replied_msg.contact.phone_number,
                'first_name': replied_msg.contact.first_name,
                'last_name': replied_msg.contact.last_name,
            }
        elif replied_msg.poll:
            await message.reply_text("❌ Polls cannot be broadcasted (Telegram limitation).")
            return
        else:
            # Text message
            broadcast_content = {
                'type': 'text',
                'text': replied_msg.text or replied_msg.caption or "No content",
                'parse_mode': ParseMode.HTML
            }
    else:
        # Text from command
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "📢 <b>Broadcast Usage:</b>\n\n"
                "<b>Method 1:</b> <code>/broadcast &lt;message&gt;</code> (supports HTML)\n"
                "<b>Method 2:</b> Reply to any message with <code>/broadcast</code>\n\n"
                "<b>Supported Types:</b>\n"
                "• 📝 Text (with HTML formatting)\n"
                "• 🖼️ Photos with captions\n" 
                "• 🎥 Videos with captions\n"
                "• 🎬 GIFs/Animations with captions\n"
                "• 📄 Documents with captions\n"
                "• 🎵 Audio with captions\n"
                "• 🎙️ Voice messages\n"
                "• 📹 Video notes\n"
                "• 🎭 Stickers\n"
                "• 📍 Locations\n"
                "• 👤 Contacts\n\n"
                "<b>HTML Tags Supported:</b>\n"
                "<code>&lt;b&gt;bold&lt;/b&gt;</code>, <code>&lt;i&gt;italic&lt;/i&gt;</code>, <code>&lt;u&gt;underline&lt;/u&gt;</code>, <code>&lt;s&gt;strikethrough&lt;/s&gt;</code>, <code>&lt;code&gt;code&lt;/code&gt;</code>, <code>&lt;pre&gt;preformatted&lt;/pre&gt;</code>, <code>&lt;a href='url'&gt;link&lt;/a&gt;</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        broadcast_content = {
            'type': 'text', 
            'text': parts[1],
            'parse_mode': ParseMode.HTML
        }
    
    try:
        # Get total user count first for progress tracking
        total_users = await mongo_client.db.users.count_documents({})
        
        if total_users == 0:
            await message.reply_text("❌ No users to broadcast to.")
            return
        
        # Start broadcast with progress tracking
        broadcast_msg = await message.reply_text(
            f"📢 <b>Starting Broadcast</b>\n"
            f"👥 Total Users: {total_users:,}\n"
            f"📊 Progress: 0%\n"
            f"📤 Sent: 0\n"
            f"❌ Failed: 0\n"
            f"⏱️ Speed: 0 msgs/sec",
            parse_mode=ParseMode.HTML
        )
        
        # Batch processing for efficiency
        import asyncio
        import time
        from datetime import datetime
        
        start_time = time.time()
        sent = 0
        failed = 0
        batch_size = 30  # Telegram rate limit friendly
        update_interval = 100  # Update progress every 100 messages
        
        # Process users in batches using cursor for memory efficiency
        cursor = mongo_client.db.users.find({}, {"user_id": 1})
        user_batch = []
        
        async def send_to_user(user_id: int) -> bool:
            """Send message to individual user."""
            try:
                if broadcast_content['type'] == 'text':
                    await client.send_message(
                        user_id, 
                        broadcast_content['text'], 
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'photo':
                    await client.send_photo(
                        user_id, 
                        broadcast_content['media'],
                        caption=broadcast_content['caption'],
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'video':
                    await client.send_video(
                        user_id, 
                        broadcast_content['media'],
                        caption=broadcast_content['caption'],
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'animation':
                    await client.send_animation(
                        user_id, 
                        broadcast_content['media'],
                        caption=broadcast_content['caption'],
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'document':
                    await client.send_document(
                        user_id, 
                        broadcast_content['media'],
                        caption=broadcast_content['caption'],
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'audio':
                    await client.send_audio(
                        user_id, 
                        broadcast_content['media'],
                        caption=broadcast_content['caption'],
                        parse_mode=broadcast_content['parse_mode']
                    )
                elif broadcast_content['type'] == 'voice':
                    await client.send_voice(
                        user_id, 
                        broadcast_content['media']
                    )
                elif broadcast_content['type'] == 'video_note':
                    await client.send_video_note(
                        user_id, 
                        broadcast_content['media']
                    )
                elif broadcast_content['type'] == 'sticker':
                    await client.send_sticker(
                        user_id, 
                        broadcast_content['media']
                    )
                elif broadcast_content['type'] == 'location':
                    await client.send_location(
                        user_id, 
                        broadcast_content['latitude'],
                        broadcast_content['longitude']
                    )
                elif broadcast_content['type'] == 'contact':
                    await client.send_contact(
                        user_id, 
                        broadcast_content['phone_number'],
                        broadcast_content['first_name'],
                        broadcast_content.get('last_name', '')
                    )
                
                return True
            except Exception as e:
                logger.debug(f"Failed to send to user {user_id}: {e}")
                return False
        
        async for user_doc in cursor:
            user_batch.append(user_doc['user_id'])
            
            # Process batch when it reaches batch_size
            if len(user_batch) >= batch_size:
                # Send to batch concurrently with rate limiting
                tasks = [send_to_user(uid) for uid in user_batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if result is True:
                        sent += 1
                    else:
                        failed += 1
                
                user_batch = []
                
                # Update progress periodically
                if (sent + failed) % update_interval == 0 or (sent + failed) == total_users:
                    elapsed = time.time() - start_time
                    speed = (sent + failed) / elapsed if elapsed > 0 else 0
                    progress = ((sent + failed) / total_users) * 100
                    
                    try:
                        await broadcast_msg.edit_text(
                            f"📢 <b>Broadcasting...</b>\n"
                            f"👥 Total Users: {total_users:,}\n"
                            f"📊 Progress: {progress:.1f}%\n"
                            f"📤 Sent: {sent:,}\n"
                            f"❌ Failed: {failed:,}\n"
                            f"⏱️ Speed: {speed:.1f} msgs/sec\n"
                            f"⏰ Elapsed: {elapsed:.0f}s",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        pass  # Don't fail broadcast if progress update fails
                
                # Rate limiting delay
                await asyncio.sleep(1)  # 1 second between batches
        
        # Process remaining users in the last batch
        if user_batch:
            tasks = [send_to_user(uid) for uid in user_batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result is True:
                    sent += 1
                else:
                    failed += 1
        
        # Final summary
        total_time = time.time() - start_time
        success_rate = (sent / total_users) * 100 if total_users > 0 else 0
        
        final_message = (
            f"✅ <b>Broadcast Completed!</b>\n"
            f"👥 Total Users: {total_users:,}\n"
            f"📤 Successfully Sent: {sent:,}\n"
            f"❌ Failed: {failed:,}\n"
            f"📊 Success Rate: {success_rate:.1f}%\n"
            f"⏰ Total Time: {total_time:.0f}s\n"
            f"⚡ Average Speed: {total_users/total_time:.1f} msgs/sec"
        )
        
        await broadcast_msg.edit_text(final_message, parse_mode=ParseMode.HTML)
        logger.info(f"Broadcast completed: {sent} sent, {failed} failed out of {total_users} users")
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        await message.reply_text("❌ Broadcast failed due to an error.")


async def restart_bot_command(client: Client, message: Message):
    """Restart bot with force pull from GitHub (Owner only)."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can restart the bot.")
        return
    
    try:
        # Send initial restart message
        restart_msg = await message.reply_text("🔄 <b>Restarting Bot...</b>\n\n⏳ Starting restart process...", parse_mode=ParseMode.HTML)
        
        # Save restart status to file for tracking
        restart_data = {
            'message_id': restart_msg.id,
            'chat_id': message.chat.id,
            'start_time': datetime.now().isoformat(),
            'status': 'starting',
            'user_id': message.from_user.id,
            'username': message.from_user.username or 'Unknown'
        }
        
        restart_file = 'restart_status.json'
        with open(restart_file, 'w', encoding='utf-8') as f:
            json.dump(restart_data, f, indent=2)
        
        # Update message with pull status
        await restart_msg.edit_text("🔄 <b>Restarting Bot...</b>\n\n📡 Pulling latest code from GitHub...", parse_mode=ParseMode.HTML)
        
        # Get current commit info before update
        try:
            current_commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
            
            current_commit_msg = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%s'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
        except Exception:
            current_commit = 'unknown'
            current_commit_msg = 'unknown'
        
        logger.info(f"Restart initiated by user {message.from_user.id} ({message.from_user.username})")
        logger.info(f"Current commit before restart: {current_commit[:8]} - {current_commit_msg}")
        
        # Force pull from GitHub
        try:
            # Reset any local changes
            subprocess.run(['git', 'reset', '--hard', 'HEAD'], check=True, cwd=os.getcwd())
            
            # Force pull latest code
            subprocess.run(['git', 'pull', '--force', 'origin', 'main'], check=True, cwd=os.getcwd())
            
            # Get new commit info
            new_commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
            
            new_commit_msg = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%s'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
            
            new_commit_author = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%an'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
            
            new_commit_date = subprocess.check_output(
                ['git', 'log', '-1', '--pretty=%ad', '--date=relative'], 
                cwd=os.getcwd(),
                text=True
            ).strip()
            
        except subprocess.CalledProcessError as e:
            await restart_msg.edit_text(f"❌ <b>Restart Failed</b>\n\n🚫 Git pull failed: {e}", parse_mode=ParseMode.HTML)
            logger.error(f"Git pull failed during restart: {e}")
            return
        
        # Update restart status file with git info
        restart_data.update({
            'status': 'code_updated',
            'old_commit': current_commit,
            'old_commit_msg': current_commit_msg,
            'new_commit': new_commit,
            'new_commit_msg': new_commit_msg,
            'new_commit_author': new_commit_author,
            'new_commit_date': new_commit_date,
            'pull_time': datetime.now().isoformat()
        })
        
        with open(restart_file, 'w', encoding='utf-8') as f:
            json.dump(restart_data, f, indent=2)
        
        # Check if there were any changes
        if current_commit == new_commit:
            update_status = "📋 <b>No new updates</b> (already on latest)"
        else:
            update_status = f"✅ <b>Code updated successfully</b>\n📝 <b>New commit:</b> <code>{new_commit[:8]}</code>\n💬 <b>Message:</b> {new_commit_msg}\n👤 <b>Author:</b> {new_commit_author}\n⏰ <b>Date:</b> {new_commit_date}"
        
        # Final message before restart
        final_message = f"""🔄 <b>Restarting Bot...</b>

{update_status}

🔄 <b>Restarting Python process...</b>
⏳ Bot will be back online shortly!

<i>This message will be updated with restart status...</i>"""
        
        await restart_msg.edit_text(final_message, parse_mode=ParseMode.HTML)
        
        # Update final status
        restart_data.update({
            'status': 'restarting',
            'final_message_time': datetime.now().isoformat()
        })
        
        with open(restart_file, 'w', encoding='utf-8') as f:
            json.dump(restart_data, f, indent=2)
        
        logger.info(f"Restarting bot process. New commit: {new_commit[:8]} - {new_commit_msg}")
        
        # Give a moment for the message to be sent
        await asyncio.sleep(1)
        
        # Restart the bot process
        os.execv(sys.executable, ['python'] + sys.argv)
        
    except Exception as e:
        logger.error(f"Error in restart command: {e}")
        try:
            await restart_msg.edit_text(f"❌ <b>Restart Failed</b>\n\n🚫 Error: {str(e)}", parse_mode=ParseMode.HTML)
        except:
            await message.reply_text(f"❌ <b>Restart Failed</b>\n\n🚫 Error: {str(e)}", parse_mode=ParseMode.HTML)


async def check_restart_status():
    """Check and update restart status message on bot startup."""
    restart_file = 'restart_status.json'
    
    if not os.path.exists(restart_file):
        return
    
    try:
        with open(restart_file, 'r', encoding='utf-8') as f:
            restart_data = json.load(f)
        
        # Only process if restart was in progress
        if restart_data.get('status') in ['starting', 'code_updated', 'restarting']:
            from pyrogram import Client
            
            # Create a temporary client to update the message
            temp_client = Client(
                "temp_restart_client",
                bot_token=settings.bot_token,
                api_id=settings.api_id,
                api_hash=settings.api_hash
            )
            
            async with temp_client:
                # Get updated commit info
                try:
                    current_commit = subprocess.check_output(
                        ['git', 'rev-parse', 'HEAD'], 
                        cwd=os.getcwd(),
                        text=True
                    ).strip()
                    
                    current_commit_msg = subprocess.check_output(
                        ['git', 'log', '-1', '--pretty=%s'], 
                        cwd=os.getcwd(),
                        text=True
                    ).strip()
                    
                    current_commit_author = subprocess.check_output(
                        ['git', 'log', '-1', '--pretty=%an'], 
                        cwd=os.getcwd(),
                        text=True
                    ).strip()
                    
                    restart_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                except Exception:
                    current_commit = 'unknown'
                    current_commit_msg = 'unknown'
                    current_commit_author = 'unknown'
                    restart_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                
                # Prepare success message
                old_commit = restart_data.get('old_commit', 'unknown')
                new_commit = restart_data.get('new_commit', current_commit)
                
                if old_commit == new_commit:
                    update_info = "📋 <b>No new updates</b> (already on latest version)"
                else:
                    update_info = f"""✅ <b>Code updated successfully</b>
📝 <b>New commit:</b> <code>{current_commit[:8]}</code>
💬 <b>Message:</b> {current_commit_msg}  
👤 <b>Author:</b> {current_commit_author}"""
                
                success_message = f"""✅ <b>Bot Restarted Successfully!</b>

{update_info}

🔄 <b>Restart completed:</b> {restart_time}
⚡ <b>Status:</b> Bot is now online and ready!

<i>Restart initiated by @{restart_data.get('username', 'Unknown')}</i>"""
                
                # Update the original message
                await temp_client.edit_message_text(
                    chat_id=restart_data['chat_id'],
                    message_id=restart_data['message_id'],
                    text=success_message,
                    parse_mode=ParseMode.HTML
                )
                
                logger.info(f"Restart completed successfully. Updated message for restart initiated by {restart_data.get('username', 'Unknown')}")
        
        # Clean up the restart status file
        os.remove(restart_file)
        
    except Exception as e:
        logger.error(f"Error updating restart status: {e}")
        # Clean up the file even if update failed
        try:
            os.remove(restart_file)
        except:
            pass


async def cache_stats_command(client: Client, message: Message):
    """Get Redis cache statistics (Owner only)."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can view cache statistics.")
        return
    
    try:
        from infra.cache import cache_client
        
        if not cache_client._redis:
            await message.reply_text(
                "📊 <b>Cache Statistics</b>\n\n"
                "❌ Redis is not connected\n"
                "💾 Using local fallback caching",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get Redis memory info
        memory_info = await cache_client._redis.info('memory')
        stats_info = await cache_client._redis.info('stats')
        keyspace_info = await cache_client._redis.info('keyspace')
        
        # Memory stats
        used_memory = memory_info.get('used_memory_human', 'Unknown')
        used_memory_rss = memory_info.get('used_memory_rss_human', 'Unknown')
        used_memory_peak = memory_info.get('used_memory_peak_human', 'Unknown')
        mem_fragmentation_ratio = memory_info.get('mem_fragmentation_ratio', 0)
        
        # Performance stats
        keyspace_hits = stats_info.get('keyspace_hits', 0)
        keyspace_misses = stats_info.get('keyspace_misses', 0)
        instantaneous_ops_per_sec = stats_info.get('instantaneous_ops_per_sec', 0)
        
        # Calculate hit rate
        total_requests = keyspace_hits + keyspace_misses
        hit_rate = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Get key counts by namespace
        v1_keys = await cache_client._redis.keys('v1:*')
        ratelimit_keys = await cache_client._redis.keys('ratelimit:*')
        all_keys = v1_keys + ratelimit_keys
        namespace_counts = {}
        total_keys = len(all_keys)
        
        for key in all_keys:
            if key.startswith('v1:'):
                parts = key.split(':')
                if len(parts) >= 2:
                    namespace = parts[1]
                    namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
            elif key.startswith('ratelimit:'):
                namespace_counts['ratelimit'] = namespace_counts.get('ratelimit', 0) + 1
        
        # Count keys with TTL
        keys_with_ttl = 0
        for key in all_keys[:50]:  # Sample first 50 keys for performance
            ttl = await cache_client._redis.ttl(key)
            if ttl > 0:
                keys_with_ttl += 1
        
        # Estimate total keys with TTL
        if all_keys:
            keys_with_ttl = int((keys_with_ttl / min(50, total_keys)) * total_keys) if total_keys > 0 else 0
        
        # Build namespace display
        namespace_display = ""
        namespace_order = ['imdb_search', 'imdb_details', 'mdl_search', 'mdl_details', 'user_templates', 'ratelimit']
        
        for ns in namespace_order:
            count = namespace_counts.get(ns, 0)
            namespace_display += f"├ {ns}: {count}\n"
        
        # Add any additional namespaces not in the predefined list
        for ns, count in namespace_counts.items():
            if ns not in namespace_order:
                namespace_display += f"├ {ns}: {count}\n"
        
        # Remove the last ├ and replace with └
        if namespace_display:
            namespace_display = namespace_display.rstrip('\n')
            last_line_idx = namespace_display.rfind('├')
            if last_line_idx != -1:
                namespace_display = namespace_display[:last_line_idx] + '└' + namespace_display[last_line_idx + 1:]
        
        cache_stats_text = f"""📊 <b>/cache_stats</b>

<b>Memory Usage:</b>
├ Used: {used_memory}
├ RSS: {used_memory_rss}
├ Peak: {used_memory_peak}
└ Fragmentation: {mem_fragmentation_ratio:.2f}

<b>Performance:</b>
├ Hit Rate: {hit_rate:.2f}%
├ Hits: {keyspace_hits:,}
├ Misses: {keyspace_misses:,}
└ Ops/sec: {instantaneous_ops_per_sec}

<b>Keys by Type:</b>
{namespace_display}

<b>Total Keys:</b> {total_keys}
<b>Keys with TTL:</b> {keys_with_ttl}"""
        
        await message.reply_text(cache_stats_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        await message.reply_text("❌ Failed to get cache statistics.")


async def cache_analyze_command(client: Client, message: Message):
    """Analyze Redis cache for insights (Owner only)."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can analyze cache.")
        return
    
    try:
        from infra.cache import cache_client
        
        if not cache_client._redis:
            await message.reply_text(
                "🔍 <b>Cache Analysis</b>\n\n"
                "❌ Redis is not connected\n"
                "💾 Using local fallback caching",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Get all keys for analysis
        all_keys = await cache_client._redis.keys('v1:*')
        total_keys = len(all_keys)
        
        if total_keys == 0:
            await message.reply_text(
                "🔍 <b>Cache Analysis</b>\n\n"
                "📭 No keys found in cache",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Analyze keys without TTL
        keys_without_ttl = 0
        keys_with_ttl = 0
        
        # Size distribution counters
        size_very_small = 0  # < 1KB
        size_small = 0      # 1KB - 10KB
        size_medium = 0     # 10KB - 100KB
        size_large = 0      # > 100KB
        
        # Sample keys for performance (analyze up to 100 keys)
        sample_keys = all_keys[:100] if len(all_keys) > 100 else all_keys
        
        for key in sample_keys:
            # Check TTL
            ttl = await cache_client._redis.ttl(key)
            if ttl == -1:  # No TTL
                keys_without_ttl += 1
            else:
                keys_with_ttl += 1
            
            # Check size (get memory usage for this key)
            try:
                key_memory = await cache_client._redis.memory_usage(key)
                if key_memory:
                    if key_memory < 1024:  # < 1KB
                        size_very_small += 1
                    elif key_memory < 10240:  # < 10KB
                        size_small += 1
                    elif key_memory < 102400:  # < 100KB
                        size_medium += 1
                    else:  # > 100KB
                        size_large += 1
            except Exception:
                # If memory_usage fails, count as very small
                size_very_small += 1
        
        # Extrapolate to total keys if we sampled
        if len(all_keys) > 100:
            ratio = total_keys / len(sample_keys)
            keys_without_ttl = int(keys_without_ttl * ratio)
            keys_with_ttl = int(keys_with_ttl * ratio)
            size_very_small = int(size_very_small * ratio)
            size_small = int(size_small * ratio)
            size_medium = int(size_medium * ratio)
            size_large = int(size_large * ratio)
        
        # Build size distribution display
        size_display = ""
        if size_large > 0:
            size_display += f"├ > 100KB: {size_large}\n"
        if size_medium > 0:
            size_display += f"├ 10KB - 100KB: {size_medium}\n"
        if size_small > 0:
            size_display += f"├ 1KB - 10KB: {size_small}\n"
        if size_very_small > 0:
            size_display += f"└ < 1KB: {size_very_small}"
        
        # Remove trailing newline and fix last connector
        size_display = size_display.rstrip('\n')
        if size_display and '└' not in size_display:
            last_line_idx = size_display.rfind('├')
            if last_line_idx != -1:
                size_display = size_display[:last_line_idx] + '└' + size_display[last_line_idx + 1:]
        
        analysis_text = f"""🔍 <b>Cache Analysis</b>

⏰ <b>Keys without TTL:</b> {keys_without_ttl}

📊 <b>Key Size Distribution:</b>
{size_display}"""
        
        await message.reply_text(analysis_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error analyzing cache: {e}")
        await message.reply_text("❌ Failed to analyze cache.")


async def shell_command(client: Client, message: Message):
    """Execute shell commands via bot (Owner only)."""
    if message.from_user.id != settings.owner_id:
        await message.reply_text("❌ Only bot owner can execute shell commands.")
        return
    
    try:
        # Extract command from message
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            await message.reply_text(
                "🐚 <b>Shell Command Usage:</b>\n\n"
                "<b>Syntax:</b> <code>/shell &lt;command&gt;</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>/shell pip install requests</code>\n"
                "• <code>/shell ls -la</code>\n"
                "• <code>/shell git status</code>\n"
                "• <code>/shell python --version</code>\n"
                "• <code>/shell df -h</code>\n\n"
                "⚠️ <b>Security Warning:</b>\n"
                "This command has full system access. Use with extreme caution!\n\n"
                "<b>Safe Commands:</b>\n"
                "• Package management: <code>pip install/uninstall</code>\n"
                "• File operations: <code>ls</code>, <code>cat</code>, <code>head</code>, <code>tail</code>\n"
                "• System info: <code>ps</code>, <code>df</code>, <code>free</code>, <code>uname</code>\n"
                "• Git operations: <code>git status</code>, <code>git log</code>\n\n"
                "<b>Dangerous Commands:</b>\n"
                "❌ Avoid: <code>rm -rf</code>, <code>chmod 777</code>, <code>sudo su</code>, etc.",
                parse_mode=ParseMode.HTML
            )
            return
        
        command = command_parts[1].strip()
        
        # Security warning for dangerous commands
        dangerous_patterns = [
            r'\brm\s+-rf\b', r'\brm\s+.*\*', r'\bchmod\s+777\b', 
            r'\bsudo\s+su\b', r'\bmkfs\b', r'\bformat\b',
            r'\bdd\s+if=', r'\bfdisk\b', r'\bcrontab\s+-r\b',
            r'>\s*/dev/', r'\bkill\s+-9.*1\b'
        ]
        
        is_dangerous = any(re.search(pattern, command, re.IGNORECASE) for pattern in dangerous_patterns)
        
        if is_dangerous:
            await message.reply_text(
                f"⚠️ <b>Potentially Dangerous Command Detected</b>\n\n"
                f"<b>Command:</b> <code>{command}</code>\n\n"
                f"This command appears to be potentially destructive. "
                f"Please review carefully before execution.\n\n"
                f"Reply with <code>EXECUTE ANYWAY</code> to proceed or cancel this operation.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Send initial status message
        status_msg = await message.reply_text(
            f"🐚 <b>Executing Shell Command</b>\n\n"
            f"<b>Command:</b> <code>{command}</code>\n"
            f"<b>Status:</b> Running...\n\n"
            f"⏳ Please wait for output...",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"Shell command initiated by owner: {command}")
        start_time = datetime.now()
        
        # Execute command with timeout
        try:
            # Use subprocess for better control and security
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd(),
                env=os.environ.copy()
            )
            
            # Wait for completion with timeout (max 5 minutes)
            try:
                stdout, stderr = process.communicate(timeout=300)
                return_code = process.returncode
                execution_time = (datetime.now() - start_time).total_seconds()
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return_code = -1
                execution_time = 300
                stderr += "\n⚠️ Command timed out after 5 minutes"
            
        except Exception as e:
            await status_msg.edit_text(
                f"🐚 <b>Shell Command Failed</b>\n\n"
                f"<b>Command:</b> <code>{command}</code>\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"❌ Execution failed before completion",
                parse_mode=ParseMode.HTML
            )
            logger.error(f"Shell command execution failed: {e}")
            return
        
        # Prepare output message
        execution_status = "✅ Success" if return_code == 0 else f"❌ Failed (Exit Code: {return_code})"
        
        # Combine stdout and stderr
        output_parts = []
        if stdout.strip():
            output_parts.append(f"<b>📤 STDOUT:</b>\n<pre>\n{stdout.strip()}\n</pre>")
        if stderr.strip():
            output_parts.append(f"<b>📥 STDERR:</b>\n<pre>\n{stderr.strip()}\n</pre>")
        
        if not output_parts:
            output_text = "<i>(No output generated)</i>"
        else:
            output_text = "\n\n".join(output_parts)
        
        # Create result message
        result_message = f"""🐚 <b>Shell Command Executed</b>

<b>Command:</b> <code>{command}</code>
<b>Status:</b> {execution_status}
<b>Execution Time:</b> {execution_time:.2f}s
<b>Return Code:</b> {return_code}

{output_text}"""
        
        # Handle long outputs
        if len(result_message) > 4096:  # Telegram message limit
            # Send basic info first
            basic_info = f"""🐚 <b>Shell Command Executed</b>

<b>Command:</b> <code>{command}</code>
<b>Status:</b> {execution_status}
<b>Execution Time:</b> {execution_time:.2f}s
<b>Return Code:</b> {return_code}

⚠️ <b>Output too long - sending as file...</b>"""
            
            await status_msg.edit_text(basic_info, parse_mode=ParseMode.HTML)
            
            # Create output file
            output_filename = f"shell_output_{int(start_time.timestamp())}.txt"
            full_output = f"Shell Command: {command}\n"
            full_output += f"Executed at: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            full_output += f"Return Code: {return_code}\n"
            full_output += f"Execution Time: {execution_time:.2f}s\n"
            full_output += "=" * 50 + "\n\n"
            
            if stdout.strip():
                full_output += "STDOUT:\n" + stdout + "\n\n"
            if stderr.strip():
                full_output += "STDERR:\n" + stderr + "\n"
            
            # Write to temp file and send
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(full_output)
            
            await message.reply_document(
                output_filename,
                caption=f"📄 Shell command output\n<b>Command:</b> <code>{command}</code>",
                parse_mode=ParseMode.HTML
            )
            
            # Clean up temp file
            os.remove(output_filename)
        else:
            # Send normal message
            await status_msg.edit_text(result_message, parse_mode=ParseMode.HTML)
        
        logger.info(f"Shell command completed: {command} (exit code: {return_code}, time: {execution_time:.2f}s)")
        
    except Exception as e:
        logger.error(f"Error in shell command: {e}")
        try:
            await status_msg.edit_text(
                f"🐚 <b>Shell Command Error</b>\n\n"
                f"<b>Command:</b> <code>{command if 'command' in locals() else 'Unknown'}</code>\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"❌ Unexpected error occurred",
                parse_mode=ParseMode.HTML
            )
        except:
            await message.reply_text(
                f"🐚 <b>Shell Command Error</b>\n\n"
                f"<b>Error:</b> {str(e)}\n\n"
                f"❌ Failed to execute shell command",
                parse_mode=ParseMode.HTML
            )