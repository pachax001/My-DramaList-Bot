from bot.logger.logger import logger

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import MONGO_URI, DB_NAME



try:
    # Initialize MongoDB client and database
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)  # Timeout after 5 seconds
    db = client[DB_NAME]

    # Test connection
    client.admin.command('ping')
    logger.info("MongoDB connection succeeded.")

except ConnectionFailure as e:
    logger.error(f"MongoDB connection failed: {e}")
    client = None
    db = None
