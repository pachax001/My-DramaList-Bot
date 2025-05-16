from datetime import datetime
from bot.logger.logger import logger
from bot.db.main_db import db
import sys
if db is None:
    logger.error("MongoDB connection is not available.")
    sys.exit(1)
else:
    broadcast_log_collection = db["broadcast_logs"]

async def log_broadcast_result(content: dict, sent_count: int, failed_count: int, failed_users: list):
    """Save structured broadcast results in the database."""
    try:
        # Create text representation for logging
        message_text = ""
        if content['media_type'] == 'text':
            message_text = content.get('text', '')
        else:
            message_text = content.get('caption', f"[{content['media_type'].capitalize()} Media]")

        broadcast_log = {
            "content": content,  # Store the full content dictionary
            "text": message_text,
            "media_type": content['media_type'],
            "sent_count": sent_count,
            "failed_count": failed_count,
            "failed_users": failed_users,
            "timestamp": datetime.utcnow(),
        }

        # Async database operation
        db.broadcast_logs.insert_one(broadcast_log)
        logger.info(f"📄 Broadcast log saved ({content['media_type']} media)")

    except Exception as e:
        logger.error(f"❌ Failed to log broadcast result: {e}")
        logger.debug(f"Problematic content: {content}")
