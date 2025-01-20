from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
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
