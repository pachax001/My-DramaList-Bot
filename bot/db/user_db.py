from bot.logger.logger import logger
from bot.db.main_db import db
import sys
from datetime import datetime, timedelta

if db is None:
    logger.error("MongoDB connection is not available.")
    sys.exit(1)
else:
    users_collection = db["users"]

def add_or_update_user(user_id, username, full_name):
    """Add or update a user with the latest interaction timestamp."""
    existing_user = users_collection.find_one({"user_id": user_id})

    if existing_user:
        # Update last active timestamp
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.utcnow(), "username": username, "full_name": full_name}}
        )
    else:
        # Add new user with join date
        user_data = {
            "user_id": user_id,
            "username": username,
            "full_name": full_name,
            "joined_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        users_collection.insert_one(user_data)

def get_total_users():
    """Get the total number of users in the database."""
    return users_collection.count_documents({})

def get_recent_users(days=7):
    """Get the count of users who interacted with the bot in the last 'days' days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return users_collection.count_documents({"last_active": {"$gte": cutoff_date}})

def get_all_users():
    """Fetch all user IDs from the database."""
    return users_collection.find({}, {"user_id": 1})


def set_user_template(user_id: int, template: str):
    """Sets or updates a user's drama details template in MongoDB."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"template": template}},
        upsert=True
    )

def get_user_template(user_id: int) -> str:
    """Retrieves a user's custom template from MongoDB, returns None if not found."""
    user = users_collection.find_one({"user_id": user_id}, {"template": 1})
    return user.get("template") if user else None

def remove_user_template(user_id: int):
    """Removes the user's custom template from the database."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$unset": {"template": ""}}
    )

def set_user_imdb_template(user_id: int, template: str):
    """Sets or updates a user's drama details template in MongoDB."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"imdb_template": template}},
        upsert=True
    )

def get_user_imdb_template(user_id: int) -> str:
    """Retrieves a user's custom template from MongoDB, returns None if not found."""
    user = users_collection.find_one({"user_id": user_id}, {"imdb_template": 1})
    return user.get("imdb_template") if user else None

def remove_user_imdb_template(user_id: int):
    """Removes the user's custom template from the database."""
    users_collection.update_one(
        {"user_id": user_id},
        {"$unset": {"imdb_template": ""}}
    )