"""12-factor configuration management."""

import sys
from typing import Any, Optional

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load environment from .env file if it exists, but prioritize actual env vars
load_dotenv(override=False)


class Settings(BaseSettings):
    """Application configuration following 12-factor principles."""
    
    # Telegram Bot
    bot_token: str = ""
    api_id: int = 0
    api_hash: str = ""
    owner_id: int = 0
    
    # Database
    mongo_uri: str = ""
    db_name: str = "mydramalist_bot_db"
    redis_url: str = "redis://localhost:6379/0"
    
    # External APIs
    mydramalist_api_url: str = "https://kuryana.tbdh.app/search/q/{}"
    mydramalist_details_url: str = "https://kuryana.tbdh.app/id/{}"
    
    # Features
    is_public: bool = False
    force_sub_channel_id: Optional[str] = None
    force_sub_channel_url: str = "https://t.me/kdramaworld_ongoing"
    
    # Performance
    http_timeout: int = 30
    max_connections: int = 100
    cache_ttl: int = 3600  # 1 hour default
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @field_validator('api_id', mode='before')
    @classmethod
    def parse_api_id(cls, v: Any) -> int:
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @field_validator('owner_id', mode='before')
    @classmethod
    def parse_owner_id(cls, v: Any) -> int:
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    def validate_required(self) -> None:
        """Validate required configuration."""
        missing = []
        
        if not self.bot_token:
            missing.append("BOT_TOKEN")
        if not self.api_id or self.api_id <= 0:
            missing.append("API_ID")
        if not self.api_hash:
            missing.append("API_HASH")
        if not self.owner_id or self.owner_id <= 0:
            missing.append("OWNER_ID")
        if not self.mongo_uri:
            missing.append("MONGO_URI")
            
        if missing:
            print(f"\n[ERROR] Missing required environment variables: {', '.join(missing)}")
            print("Please set these in your environment or .env file.")
            sys.exit(1)
    
    class Config:
        env_prefix = ""
        case_sensitive = False
        # Pydantic V2 compatibility
        extra = 'ignore'


# Global settings instance
settings = Settings()
settings.validate_required()