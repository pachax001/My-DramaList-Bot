"""User authorization handlers."""

from pyrogram import Client
from pyrogram.types import Message
from infra.config import settings
from infra.logging import get_logger
from infra.db import mongo_client

logger = get_logger(__name__)


async def authorize_cmd(client: Client, message: Message):
    """Authorize a user to use the bot."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can authorize users.")
    
    parts = message.text.split()
    if len(parts) != 2:
        return await message.reply_text("Usage: /authorize <user_id>")
    
    try:
        user_id = int(parts[1])
        
        # Add to authorized users collection
        await mongo_client.db.authorized_users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "authorized": True}},
            upsert=True
        )
        
        logger.info(f"User {user_id} authorized by owner {settings.owner_id}")
        await message.reply_text(f"✅ User {user_id} has been authorized.")
        
    except ValueError:
        await message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error authorizing user: {e}")
        await message.reply_text("❌ Failed to authorize user.")


async def unauthorize_cmd(client: Client, message: Message):
    """Remove user authorization."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can unauthorize users.")
    
    parts = message.text.split()
    if len(parts) != 2:
        return await message.reply_text("Usage: /unauthorize <user_id>")
    
    try:
        user_id = int(parts[1])
        
        # Remove from authorized users
        result = await mongo_client.db.authorized_users.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"User {user_id} unauthorized by owner {settings.owner_id}")
            await message.reply_text(f"✅ User {user_id} has been unauthorized.")
        else:
            await message.reply_text(f"ℹ️ User {user_id} was not authorized.")
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID format.")
    except Exception as e:
        logger.error(f"Error unauthorizing user: {e}")
        await message.reply_text("❌ Failed to unauthorize user.")


async def list_users_cmd(client: Client, message: Message):
    """List all authorized users."""
    if message.from_user.id != settings.owner_id:
        return await message.reply_text("❌ Only bot owner can view user list.")
    
    try:
        # Get authorized users
        authorized_users = []
        async for user in mongo_client.db.authorized_users.find():
            authorized_users.append(user["user_id"])
        
        # Get total registered users
        total_users = await mongo_client.db.users.count_documents({})
        
        if authorized_users:
            user_list = "\n".join([f"• {uid}" for uid in authorized_users])
            text = f"👥 **Authorized Users** ({len(authorized_users)}):\n{user_list}\n\n📊 Total registered users: {total_users}"
        else:
            text = f"ℹ️ No authorized users.\n📊 Total registered users: {total_users}"
        
        await message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await message.reply_text("❌ Failed to get user list.")