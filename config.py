import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from bot.logger.logger import logger
# Load environment variables from config.env
load_dotenv('config.env')

# Read environment variables with defaults or raise an error if critical values are missing
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_ID = os.getenv("API_ID", "").strip()
API_HASH = os.getenv("API_HASH", "").strip()
OWNER_ID = os.getenv("OWNER_ID", "").strip()
IS_PUBLIC_ENV = os.getenv("IS_PUBLIC", "false").lower() == "true"

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "mydramalist_bot_db").strip()

# MyDramaList API endpoints

API_URL = os.getenv("API_URL", "https://kuryana.vercel.app/search/q/{}").strip()
DETAILS_API_URL = os.getenv("DETAILS_API_URL", "https://kuryana.vercel.app/id/{}").strip()


def validate_config():
    """Validates required configuration values."""
    missing_vars = []

    if not BOT_TOKEN:
        missing_vars.append("BOT_TOKEN")
    if not API_ID.isdigit() or int(API_ID) <= 0:
        missing_vars.append("API_ID (must be a positive integer)")
    if not API_HASH:
        missing_vars.append("API_HASH")
    if not OWNER_ID.isdigit() or int(OWNER_ID) <= 0:
        missing_vars.append("OWNER_ID (must be a positive integer)")
    if not MONGO_URI:
        missing_vars.append("MONGO_URI")
    if not DB_NAME:
        missing_vars.append("DB_NAME")

    if missing_vars:
        print("\n[ERROR] Missing or invalid configuration values:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease check your `config.env` file and set the required values.")
        sys.exit(1)


# Call the validation function when the module is loaded
validate_config()

# Convert types after validation
API_ID = int(API_ID)
OWNER_ID = int(OWNER_ID)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
settings_collection = db["settings"]

def get_public_mode():
    """Retrieve the current public mode status from the database."""
    setting = settings_collection.find_one({"key": "public_mode"})
    return setting["value"] if setting else None

def set_public_mode(status: bool):
    """Store the public mode status in the database."""
    settings_collection.update_one(
        {"key": "public_mode"},
        {"$set": {"value": status}},
        upsert=True
    )


# -------------------------------------------------------------------
# Initialize and Synchronize IS_PUBLIC with Database
# -------------------------------------------------------------------

# Check if IS_PUBLIC is already in the database
db_public_mode = get_public_mode()

def initialize_settings():
    """Ensure required settings are stored in the database when bot starts."""
    if get_public_mode() is None:
        logger.info("🔧 IS_PUBLIC not found in the database. Initializing...")
        set_public_mode(IS_PUBLIC_ENV)
    else:
        logger.info("🔧 IS_PUBLIC found in the database. Synchronizing...")