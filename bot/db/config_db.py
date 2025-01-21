from bot.logger.logger import logger
from bot.db.main_db import db
import sys
if db is None:
    logger.error("MongoDB connection is not available.")
    sys.exit(1)
else:
    settings_collection = db["settings"]

def set_public_mode(status: bool):
    """Set the bot public mode status (True for on, False for off)."""
    settings_collection.update_one(
        {"key": "public_mode"},
        {"$set": {"value": status}},
        upsert=True
    )

def get_public_mode():
    """Retrieve the current public mode status."""
    setting = settings_collection.find_one({"key": "public_mode"})
    return setting["value"] if setting else False  # Default to False if not found
