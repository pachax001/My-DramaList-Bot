from pymongo import MongoClient
from datetime import datetime
from config import MONGO_URI, DB_NAME
from bot.logger.logger import logger

# Initialize MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
broadcast_log_collection = db["broadcast_logs"]

def log_broadcast_result(message: str, sent_count: int, failed_count: int, failed_users: list):
    """Save the broadcast results in the database for tracking."""
    try:
        broadcast_log = {
            "message": message,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "failed_users": failed_users,
            "timestamp": datetime.utcnow(),
        }

        broadcast_log_collection.insert_one(broadcast_log)
        logger.info("📄 Broadcast results saved to database successfully.")

    except Exception as e:
        logger.error(f"❌ Failed to log broadcast result: {e}")
