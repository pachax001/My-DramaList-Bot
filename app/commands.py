"""Bot command definitions and management."""

from typing import List
from pyrogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from infra.logging import get_logger
from infra.config import settings

logger = get_logger(__name__)


class BotCommandManager:
    """Manages bot command registration and updates."""
    
    @staticmethod
    def get_public_commands() -> List[BotCommand]:
        """Get commands available to all users in public mode."""
        return [
            BotCommand("start", "Start the bot and see main menu"),
            BotCommand("help", "Show detailed help and command guide"),
            
            # Search commands
            BotCommand("mdl", "Search MyDramaList or process MDL URL"),
            BotCommand("imdb", "Search IMDB or process IMDB URL"),
            BotCommand("mdlurl", "Get drama details from MyDramaList URL"),
            BotCommand("imdburl", "Get movie/show details from IMDB URL"),
            
            # Template commands
            BotCommand("setmdltemplate", "Set custom MyDramaList template"),
            BotCommand("getmdltemplate", "View your current MDL template"),
            BotCommand("removemdltemplate", "Remove your MDL template"),
            BotCommand("previewmdltemplate", "Preview your MDL template"),
            BotCommand("mdlplaceholders", "Show all MyDramaList placeholders"),
            
            BotCommand("setimdbtemplate", "Set custom IMDB template"),
            BotCommand("getimdbtemplate", "View your current IMDB template"),
            BotCommand("removeimdbtemplate", "Remove your IMDB template"),
            BotCommand("previewimdbtemplate", "Preview your IMDB template"),
            BotCommand("imdbplaceholders", "Show all IMDB placeholders"),
        ]
    
    @staticmethod
    def get_private_commands() -> List[BotCommand]:
        """Get commands available in private mode (limited set)."""
        return [
            BotCommand("start", "Start the bot and see main menu"),
            BotCommand("help", "Show detailed help and command guide"),
        ]
    
    @staticmethod
    def get_owner_commands() -> List[BotCommand]:
        """Get all commands including owner-specific ones."""
        base_commands = BotCommandManager.get_public_commands()
        owner_only_commands = [
            BotCommand("authorize", "Grant bot access to a user"),
            BotCommand("unauthorize", "Remove bot access from a user"),
            BotCommand("users", "View authorized users list"),
            BotCommand("userstats", "Get bot usage statistics"),
            BotCommand("setpublicmode", "Toggle public mode on/off"),
            BotCommand("broadcast", "Send message to all users"),
            BotCommand("log", "Get bot log files"),
            BotCommand("health", "Check service health status"),
            BotCommand("cachereload", "Clear all caches and restart cache client"),
            BotCommand("restart", "Force update from GitHub and restart bot"),
        ]
        return base_commands + owner_only_commands
    
    @staticmethod
    async def setup_commands(app, owner_id: int, is_public: bool = True) -> bool:
        """Set up bot commands based on current mode."""
        try:
            # Choose commands based on public/private mode
            user_commands = BotCommandManager.get_public_commands() if is_public else BotCommandManager.get_private_commands()
            owner_commands = BotCommandManager.get_owner_commands()
            
            # Set commands for regular users
            await app.set_bot_commands(user_commands, scope=BotCommandScopeDefault())
            logger.info(f"Registered {len(user_commands)} commands for {'public' if is_public else 'private'} mode")
            
            # Set enhanced commands for owner
            await app.set_bot_commands(owner_commands, scope=BotCommandScopeChat(chat_id=owner_id))
            logger.info(f"Registered {len(owner_commands)} commands for owner")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set bot commands: {e}")
            return False
    
    @staticmethod
    async def update_commands_for_mode_change(app, owner_id: int, new_public_mode: bool) -> bool:
        """Update bot commands when public/private mode changes."""
        try:
            logger.info(f"Updating bot commands for {'public' if new_public_mode else 'private'} mode")
            return await BotCommandManager.setup_commands(app, owner_id, new_public_mode)
        except Exception as e:
            logger.error(f"Failed to update commands for mode change: {e}")
            return False