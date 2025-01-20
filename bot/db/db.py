# db.py
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
from datetime import datetime
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["authorized_users"]  # Collection name of your choice
public_collection = db["public"]  # Collection name of your choice


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


