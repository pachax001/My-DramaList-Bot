"""Cached template service for retrieving user templates."""

from typing import Optional
from infra.cache import cache_client
from infra.db import mongo_client
from infra.logging import get_logger

logger = get_logger(__name__)


class CachedTemplateService:
    """Service for retrieving user templates with caching."""
    
    @staticmethod
    async def get_user_mdl_template(user_id: int) -> Optional[str]:
        """Get user's MyDramaList template with caching."""
        cache_key = f"mdl_{user_id}"
        
        # Try cache first
        template = await cache_client.get("user_templates", cache_key)
        
        if template is None:
            # Cache miss, get from database
            try:
                template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
                if template_doc:
                    template = template_doc.get("template", "")
                    # Cache the template for 2 hours
                    await cache_client.set("user_templates", cache_key, template, ttl=7200)
                    logger.debug(f"Cached MDL template for user {user_id}")
                else:
                    # Cache negative result for 30 minutes to avoid repeated DB queries
                    await cache_client.set("user_templates", cache_key, "", ttl=1800)
                    logger.debug(f"No MDL template found for user {user_id}, cached empty result")
            except Exception as e:
                logger.error(f"Error retrieving MDL template for user {user_id}: {e}")
                return None
        
        return template if template else None
    
    @staticmethod
    async def get_user_imdb_template(user_id: int) -> Optional[str]:
        """Get user's IMDB template with caching."""
        cache_key = f"imdb_{user_id}"
        
        # Try cache first
        template = await cache_client.get("user_templates", cache_key)
        
        if template is None:
            # Cache miss, get from database
            try:
                template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
                if template_doc:
                    template = template_doc.get("template", "")
                    # Cache the template for 2 hours
                    await cache_client.set("user_templates", cache_key, template, ttl=7200)
                    logger.debug(f"Cached IMDB template for user {user_id}")
                else:
                    # Cache negative result for 30 minutes to avoid repeated DB queries
                    await cache_client.set("user_templates", cache_key, "", ttl=1800)
                    logger.debug(f"No IMDB template found for user {user_id}, cached empty result")
            except Exception as e:
                logger.error(f"Error retrieving IMDB template for user {user_id}: {e}")
                return None
        
        return template if template else None
    
    @staticmethod
    async def invalidate_user_templates(user_id: int) -> None:
        """Invalidate all templates for a user."""
        try:
            await cache_client.delete("user_templates", f"mdl_{user_id}")
            await cache_client.delete("user_templates", f"imdb_{user_id}")
            logger.info(f"Invalidated all templates for user {user_id}")
        except Exception as e:
            logger.warning(f"Error invalidating templates for user {user_id}: {e}")


# Global instance
cached_template_service = CachedTemplateService()