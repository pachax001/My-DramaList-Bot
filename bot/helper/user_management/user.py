from bot.logger.logger import logger
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from bot.db.db import (
    is_user_authorized,
    authorize_user,
    unauthorize_user,
    load_authorized_users  # only if needed for listing
)


async def authorize_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Usage: /authorize user_id")

    try:
        new_user_id = int(parts[1])
        if is_user_authorized(new_user_id):
            await message.reply_text(f"User {new_user_id} is already authorized.")
        else:
            authorize_user(new_user_id)
            await message.reply_text(f"User {new_user_id} has been authorized.")
    except ValueError:
        await message.reply_text("Invalid user ID. Must be an integer.")


async def unauthorize_cmd(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Usage: /unauthorize user_id")

    try:
        user_id_to_remove = int(parts[1])
        if user_id_to_remove == OWNER_ID:
            return await message.reply_text("You cannot unauthorize the owner.")
        
        if not is_user_authorized(user_id_to_remove):
            await message.reply_text(f"User {user_id_to_remove} is not authorized.")
        else:
            unauthorize_user(user_id_to_remove)
            await message.reply_text(f"User {user_id_to_remove} has been unauthorized.")
    except ValueError:
        await message.reply_text("Invalid user ID. Must be an integer.")


async def list_users_cmd(client: Client, message: Message):
    """Owner can see all authorized users (file-based)."""
    users = load_authorized_users()
    if not users:
        await message.reply_text("No users are currently authorized.")
    else:
        txt = "Authorized Users:\n" + "\n".join(str(u) for u in users)
        await message.reply_text(txt)