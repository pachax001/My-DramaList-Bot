from bot.db.main_db import db
from bot.logger.logger import logger
import sys

if db is None:
    logger.error("MongoDB connection is not available.")
    sys.exit(1)
else:
    users_collection = db["authorized_users"]  # Collection name of your choice



def is_user_authorized(user_id: int) -> bool:
    """
    Checks if a user is authorized by looking in the MongoDB collection.
    """
    doc = users_collection.find_one({"user_id": user_id})
    return doc is not None


def authorize_user(user_id: int) -> None:
    """
    Inserts a user into the MongoDB collection if not already present.
    """
    if not is_user_authorized(user_id):
        users_collection.insert_one({"user_id": user_id})


def unauthorize_user(user_id: int) -> None:
    """
    Removes a user from the MongoDB collection.
    """
    users_collection.delete_one({"user_id": user_id})


def load_authorized_users() -> list[int]:
    """
    Returns a list of all authorized user IDs.
    """
    cursor = users_collection.find({}, {"_id": 0, "user_id": 1})
    return [doc["user_id"] for doc in cursor]




