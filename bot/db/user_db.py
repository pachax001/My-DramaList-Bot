from pymongo import MongoClient
from datetime import datetime, timedelta
from config import MONGO_URI, DB_NAME

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
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
