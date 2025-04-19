from bot.db.authorized_db import is_user_authorized
from config import OWNER_ID, FORCE_SUB_CHANNEL_ID
from bot.db.config_db import get_public_mode
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from bot.logger.logger import logger
from pyrogram.errors import  UserNotParticipant
async def is_subscribed(client: Client, user_id: int) -> bool:
    """
    Returns True if the user is a member (or above) of the FORCE_SUB_CHANNEL.
    """
    if FORCE_SUB_CHANNEL_ID is None:
        return True
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL_ID, user_id=user_id)
        return member.status in (ChatMemberStatus.MEMBER,ChatMemberStatus.ADMINISTRATOR,ChatMemberStatus.OWNER)
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.exception(f"Issue with is_subscribed {e}")
        return False

async def user_can_use_bot(user_id: int) -> bool:
    """
    If IS_PUBLIC is True, any user can use the bot.
    Otherwise, only the owner or authorized users are allowed.
    """
    if user_id == OWNER_ID:
        return True
    if get_public_mode():
        return True
    return is_user_authorized(user_id)