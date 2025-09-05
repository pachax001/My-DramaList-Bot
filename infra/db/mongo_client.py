"""Async MongoDB client with connection pooling."""

from typing import Optional

import motor.motor_asyncio
from pymongo.errors import ConnectionFailure

from infra.config import settings
from infra.logging import get_logger

logger = get_logger(__name__)


class MongoClient:
    """Async MongoDB client with connection pooling."""
    
    def __init__(self):
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
    
    async def start(self):
        """Initialize MongoDB connection."""
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.mongo_uri,
                maxPoolSize=settings.max_connections,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=settings.http_timeout * 1000,
                connectTimeoutMS=settings.http_timeout * 1000,
            )
            
            self._db = self._client[settings.db_name]
            
            # Test connection
            await self._client.admin.command('ping')
            logger.info("MongoDB connection established with connection pooling")
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            self._client = None
            self._db = None
            raise
    
    async def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")
    
    @property
    def db(self) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        """Get database instance."""
        if self._db is None:
            raise RuntimeError("MongoDB not connected. Call start() first.")
        return self._db
    
    async def health_check(self) -> bool:
        """Check if MongoDB is healthy."""
        try:
            if self._client is None:
                return False
            await self._client.admin.command('ping')
            return True
        except Exception:
            return False


# Global MongoDB client
mongo_client = MongoClient()