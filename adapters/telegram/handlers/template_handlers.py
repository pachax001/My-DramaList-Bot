"""Template management handlers."""

from pyrogram import Client
from pyrogram.types import Message
from infra.logging import get_logger
from infra.db import mongo_client

logger = get_logger(__name__)


async def set_template_command(client: Client, message: Message):
    """Set MyDramaList template for user."""
    user_id = message.from_user.id
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "Usage: /setmdltemplate <template> or reply to a template message\n\n"
                "Example placeholders: {title}, {rating}, {synopsis}, {country}, {episodes}"
            )
            return
        template = parts[1]
    
    try:
        # Save template to database
        await mongo_client.db.mdl_templates.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "template": template}},
            upsert=True
        )
        
        logger.info(f"User {user_id} set MDL template")
        await message.reply_text("✅ MyDramaList template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting MDL template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_template_command(client: Client, message: Message):
    """Get user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        
        if template_doc:
            template = template_doc.get("template", "")
            await message.reply_text(f"📝 Your current MyDramaList template:\n\n`{template}`")
        else:
            await message.reply_text("ℹ️ You don't have a custom MyDramaList template set.")
            
    except Exception as e:
        logger.error(f"Error getting MDL template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_template_command(client: Client, message: Message):
    """Remove user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        result = await mongo_client.db.mdl_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"User {user_id} removed MDL template")
            await message.reply_text("✅ MyDramaList template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have a MyDramaList template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing MDL template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_template_command(client: Client, message: Message):
    """Preview user's MyDramaList template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.mdl_templates.find_one({"user_id": user_id})
        
        if not template_doc:
            await message.reply_text("ℹ️ You don't have a custom MyDramaList template set.")
            return
        
        # Mock data for preview
        mock_data = {
            "title": "Sample Drama",
            "complete_title": "Sample Drama (Complete Title)",
            "rating": "8.5",
            "synopsis": "This is a sample synopsis for preview...",
            "country": "South Korea",
            "episodes": "16",
            "genres": "🎭 Romance, 😂 Comedy",
            "year": "2023"
        }
        
        try:
            preview = template_doc["template"].format(**mock_data)
            await message.reply_text(f"👁️ **Template Preview:**\n\n{preview}")
        except KeyError as e:
            await message.reply_text(f"❌ Template error: Unknown placeholder {e}")
        except Exception as e:
            await message.reply_text(f"❌ Template formatting error: {e}")
            
    except Exception as e:
        logger.error(f"Error previewing MDL template: {e}")
        await message.reply_text("❌ Failed to preview template.")


# IMDB Template handlers
async def set_imdb_template_command(client: Client, message: Message):
    """Set IMDB template for user."""
    user_id = message.from_user.id
    
    # Get template from message
    if message.reply_to_message and message.reply_to_message.text:
        template = message.reply_to_message.text
    else:
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            await message.reply_text(
                "Usage: /setimdbtemplate <template> or reply to a template message\n\n"
                "Example placeholders: {title}, {year}, {rating}, {plot}, {cast}, {director}"
            )
            return
        template = parts[1]
    
    try:
        # Save template to database
        await mongo_client.db.imdb_templates.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "template": template}},
            upsert=True
        )
        
        logger.info(f"User {user_id} set IMDB template")
        await message.reply_text("✅ IMDB template set successfully!")
        
    except Exception as e:
        logger.error(f"Error setting IMDB template: {e}")
        await message.reply_text("❌ Failed to set template.")


async def get_imdb_template_command(client: Client, message: Message):
    """Get user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        
        if template_doc:
            template = template_doc.get("template", "")
            await message.reply_text(f"📝 Your current IMDB template:\n\n`{template}`")
        else:
            await message.reply_text("ℹ️ You don't have a custom IMDB template set.")
            
    except Exception as e:
        logger.error(f"Error getting IMDB template: {e}")
        await message.reply_text("❌ Failed to get template.")


async def remove_imdb_template_command(client: Client, message: Message):
    """Remove user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        result = await mongo_client.db.imdb_templates.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            logger.info(f"User {user_id} removed IMDB template")
            await message.reply_text("✅ IMDB template removed successfully!")
        else:
            await message.reply_text("ℹ️ You don't have an IMDB template to remove.")
            
    except Exception as e:
        logger.error(f"Error removing IMDB template: {e}")
        await message.reply_text("❌ Failed to remove template.")


async def preview_imdb_template_command(client: Client, message: Message):
    """Preview user's IMDB template."""
    user_id = message.from_user.id
    
    try:
        template_doc = await mongo_client.db.imdb_templates.find_one({"user_id": user_id})
        
        if not template_doc:
            await message.reply_text("ℹ️ You don't have a custom IMDB template set.")
            return
        
        # Mock data for preview
        mock_data = {
            "title": "Sample Movie",
            "year": "2023",
            "rating": "8.7",
            "plot": "This is a sample plot for preview purposes...",
            "cast": "Actor 1, Actor 2, Actor 3",
            "director": "Director Name",
            "genres": "🎭 Drama, 🎬 Action"
        }
        
        try:
            preview = template_doc["template"].format(**mock_data)
            await message.reply_text(f"👁️ **Template Preview:**\n\n{preview}")
        except KeyError as e:
            await message.reply_text(f"❌ Template error: Unknown placeholder {e}")
        except Exception as e:
            await message.reply_text(f"❌ Template formatting error: {e}")
            
    except Exception as e:
        logger.error(f"Error previewing IMDB template: {e}")
        await message.reply_text("❌ Failed to preview template.")