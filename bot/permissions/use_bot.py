from bot.db.db import is_user_authorized
from config import OWNER_ID
from bot.db.config_db import get_public_mode


def user_can_use_bot(user_id: int) -> bool:
    """
    If IS_PUBLIC is True, any user can use the bot.
    Otherwise, only the owner or authorized users are allowed.
    """
    if user_id == OWNER_ID:
        return True
    if get_public_mode():
        return True
    return is_user_authorized(user_id)