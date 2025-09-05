"""High-performance Telegram bot with layered architecture."""

import asyncio
import os
import signal
import sys
from pyrogram import Client
from pyrogram.types import BotCommand
from pyrogram.enums import ParseMode

# Enable uvloop on POSIX systems for better performance
if os.name == "posix":
    try:
        import uvloop
        if sys.platform.startswith(("linux", "darwin")):
            uvloop.install()
    except Exception:
        pass  # Continue without uvloop if unavailable
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

# Infrastructure
from infra.config import settings
from infra.logging import get_logger
from infra.http import http_client
from infra.cache import cache_client
from infra.db import mongo_client

# Middleware  
from app.middleware import monitor_performance, HealthChecker
from app.commands import BotCommandManager

# Handlers (new architecture)
from adapters.telegram.handlers.auth_handlers import authorize_cmd, unauthorize_cmd, list_users_cmd
from adapters.telegram.handlers.basic_handlers import start_command, send_log, help_command, user_stats_command, set_public_mode_command, manual_broadcast_command, cache_reload_command, restart_bot_command, check_restart_status, shell_command
from adapters.telegram.handlers.search_handlers import (search_dramas_command, drama_details_callback, close_search_results,
    search_imdb, imdb_details_callback, handle_drama_url, handle_imdb_url)
from adapters.telegram.handlers.template_handlers import (set_template_command, get_template_command, remove_template_command, preview_template_command,
    set_imdb_template_command, get_imdb_template_command, remove_imdb_template_command, preview_imdb_template_command,
    mdl_placeholders_command, imdb_placeholders_command)
from pyrogram import filters

logger = get_logger(__name__)


class HighPerformanceBot:
    """High-performance bot with async lifecycle management."""
    
    def __init__(self) -> None:
        self.app = Client(
            "mydramalist_bot",
            bot_token=settings.bot_token,
            api_id=settings.api_id,
            api_hash=settings.api_hash
        )
        self.is_running = False
    
    async def start_services(self) -> None:
        """Start all services with proper initialization order."""
        logger.info("Starting services...")
        
        try:
            # Start HTTP client first
            await http_client.start()
            
            # Start cache client
            await cache_client.start()
            
            # Start database
            await mongo_client.start()
            
            logger.info("All services started successfully")
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            await self.stop_services()  # Cleanup on failure
            raise
    
    async def stop_services(self) -> None:
        """Gracefully stop all services."""
        logger.info("Stopping services...")
        
        # Stop in reverse order with error handling
        errors = []
        
        try:
            await mongo_client.close()
        except Exception as e:
            errors.append(f"MongoDB: {e}")
        
        try:
            await cache_client.close()
        except Exception as e:
            errors.append(f"Redis: {e}")
        
        try:
            await http_client.close()
        except Exception as e:
            errors.append(f"HTTP: {e}")
        
        if errors:
            logger.warning(f"Service shutdown errors: {'; '.join(errors)}")
        
        logger.info("All services stopped")
    
    def setup_handlers(self) -> None:
        """Register all handlers with performance monitoring."""
        
        # Apply performance monitoring to key handlers
        monitored_start = monitor_performance("start_command")(start_command)
        monitored_search_dramas = monitor_performance("search_dramas")(search_dramas_command)
        monitored_search_imdb = monitor_performance("search_imdb")(search_imdb)
        monitored_drama_details = monitor_performance("drama_details")(drama_details_callback)
        monitored_imdb_details = monitor_performance("imdb_details")(imdb_details_callback)
        
        # Authorization handlers (Owner only)
        self.app.add_handler(MessageHandler(authorize_cmd, filters.command("authorize") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(unauthorize_cmd, filters.command("unauthorize") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(list_users_cmd, filters.command("users") & filters.user(settings.owner_id)))
        
        # Core handlers
        self.app.add_handler(MessageHandler(monitored_start, filters.command("start")))
        self.app.add_handler(MessageHandler(help_command, filters.command("help")))
        
        # Search handlers  
        self.app.add_handler(MessageHandler(monitored_search_dramas, filters.command("mdl")))
        self.app.add_handler(MessageHandler(monitored_search_imdb, filters.command("imdb")))
        
        # URL handlers
        self.app.add_handler(MessageHandler(handle_drama_url, filters.command("mdlurl")))
        self.app.add_handler(MessageHandler(handle_imdb_url, filters.command("imdburl")))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(monitored_drama_details, filters.regex("^details")))
        self.app.add_handler(CallbackQueryHandler(monitored_imdb_details, filters.regex("^imdbdetails")))
        self.app.add_handler(CallbackQueryHandler(close_search_results, filters.regex("^close_search")))
        
        # Template handlers
        self.app.add_handler(MessageHandler(set_template_command, filters.command("setmdltemplate")))
        self.app.add_handler(MessageHandler(get_template_command, filters.command("getmdltemplate")))
        self.app.add_handler(MessageHandler(remove_template_command, filters.command("removemdltemplate")))
        self.app.add_handler(MessageHandler(preview_template_command, filters.command("previewmdltemplate")))
        
        self.app.add_handler(MessageHandler(set_imdb_template_command, filters.command("setimdbtemplate")))
        self.app.add_handler(MessageHandler(get_imdb_template_command, filters.command("getimdbtemplate")))
        self.app.add_handler(MessageHandler(remove_imdb_template_command, filters.command("removeimdbtemplate")))
        self.app.add_handler(MessageHandler(preview_imdb_template_command, filters.command("previewimdbtemplate")))
        
        # Placeholder listing handlers
        self.app.add_handler(MessageHandler(mdl_placeholders_command, filters.command("mdlplaceholders")))
        self.app.add_handler(MessageHandler(imdb_placeholders_command, filters.command("imdbplaceholders")))
        
        # Admin handlers (Owner only)
        self.app.add_handler(MessageHandler(send_log, filters.command("log") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(user_stats_command, filters.command("userstats") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(set_public_mode_command, filters.command("setpublicmode") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(manual_broadcast_command, filters.command("broadcast") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(cache_reload_command, filters.command("cachereload") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(restart_bot_command, filters.command("restart") & filters.user(settings.owner_id)))
        self.app.add_handler(MessageHandler(shell_command, filters.command("shell") & filters.user(settings.owner_id)))
        
        
        # Health check handler
        @self.app.on_message(filters.command("health") & filters.user(settings.owner_id))
        async def health_check(client, message):
            """Health check endpoint for monitoring."""
            health_status = await HealthChecker.check_services()
            status_text = "🏥 <b>Service Health Status</b>\n\n"
            
            for service, status in health_status.items():
                emoji = "✅" if status == "healthy" else "❌"
                status_text += f"{emoji} <b>{service.title()}:</b> {status}\n"
            
            await message.reply_text(status_text, parse_mode=ParseMode.HTML)
        
        logger.info("All handlers registered with performance monitoring")
    
    async def setup_bot_commands(self) -> None:
        """Set up bot commands in Telegram's command menu."""
        try:
            # Get current public mode status from database
            public_setting = await mongo_client.db.settings.find_one({"key": "public_mode"})
            is_public = public_setting.get("value", True) if public_setting else settings.is_public
            
            # Setup commands using the command manager
            success = await BotCommandManager.setup_commands(self.app, settings.owner_id, is_public)
            
            if success:
                logger.info("✅ Bot commands registered successfully")
            else:
                logger.warning("⚠️ Bot command registration had issues")
                
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
            # Don't fail startup if command registration fails
    
    def setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        def signal_handler(sig: int, frame) -> None:
            logger.info(f"Received signal {sig}, initiating graceful shutdown...")
            self.is_running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self) -> None:
        """Run the bot with proper lifecycle management."""
        try:
            self.setup_signal_handlers()
            await self.start_services()
            self.setup_handlers()
            
            logger.info("Starting Telegram bot...")
            await self.app.start()
            
            # Setup bot commands in Telegram menu
            await self.setup_bot_commands()
            
            # Check and update restart status if bot was restarted
            await check_restart_status()
            
            self.is_running = True
            
            logger.info("🚀 High-performance bot is running with:")
            logger.info(f"  - uvloop: {'enabled' if 'uvloop' in sys.modules else 'disabled'}")
            logger.info(f"  - Async HTTP client with {settings.max_connections} max connections")
            logger.info(f"  - Redis caching with {settings.cache_ttl}s TTL")
            logger.info(f"  - MongoDB connection pooling")
            logger.info(f"  - Performance monitoring enabled")
            
            # Keep running until shutdown signal
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            raise
        finally:
            logger.info("Initiating graceful shutdown...")
            try:
                await self.app.stop()
            except Exception as e:
                logger.error(f"Error stopping Telegram client: {e}")
            await self.stop_services()
            logger.info("Bot shutdown complete")


async def main() -> None:
    """Main entry point."""
    bot = HighPerformanceBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)