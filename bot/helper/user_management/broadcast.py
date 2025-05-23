import asyncio
from pyrogram import Client
from pyrogram.enums import ParseMode
from bot.db.user_db import get_all_users
from bot.logger.logger import logger
from bot.db.broadcast_db import log_broadcast_result
from pyrogram.types import Message
# Configure logging


async def broadcast_to_users(client: Client, message: dict, broadcast_message: Message ,batch_size=20, delay=1.5, ):
    """
    Broadcast messages to all users in batches to avoid hitting Telegram's rate limits.
    
    Args:
        client (Client): The Pyrogram client.
        message (str): The message to be sent.
        broadcast_message (str): The message with broadcasting details.
        batch_size (int): Number of users to send messages to in each batch.
        delay (float): Delay (in seconds) between each batch to avoid flooding.

    """
    users = list(get_all_users())  # Convert cursor to list
    total_users = len(users)
    sent_count = 0
    failed_count = 0
    failed_users = []

    logger.info(f"📢 Starting broadcast to {total_users} users in batches of {batch_size}...")
    await client.edit_message_text(chat_id=broadcast_message.chat.id,message_id=broadcast_message.id,text=f"📢 Broadcasting to {total_users} users in batches of {batch_size}...")


    # Process users in batches
    for i in range(0, total_users, batch_size):
        batch = users[i:i + batch_size]
        tasks = []
        
        for user in batch:
            user_id = user["user_id"]
            tasks.append(send_media_message(client, user_id, message, failed_users))

        # Execute tasks concurrently
        results = await asyncio.gather(*tasks)

        # Count sent and failed messages
        sent_count += sum(1 for result in results if result)
        failed_count += sum(1 for result in results if not result)

        logger.info(f"📤 Sent: {sent_count}, ❌ Failed: {failed_count}")

        # Introduce delay after processing each batch
        await asyncio.sleep(delay)

    logger.info(f"✅ Broadcast completed: {sent_count} messages sent, {failed_count} failed.")

    await asyncio.sleep(2)
    await client.edit_message_text(chat_id=broadcast_message.chat.id,message_id=broadcast_message.id,text=f"✅ Broadcast completed: {sent_count} messages sent, {failed_count} failed.")

    # Log broadcast results in database
    await log_broadcast_result(message, sent_count, failed_count, failed_users)

async def send_message(client, user_id, message, failed_users):
    """
    Send a message to an individual user.
    
    Args:
        client (Client): The Pyrogram client.
        user_id (int): The user's Telegram ID.
        message (str): The message to be sent.
        failed_users (list): List to track failed user IDs.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        await client.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.HTML)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send message to {user_id}: {e}")
        failed_users.append(user_id)
        return False


async def send_media_message(client, user_id, content, failed_users):
    """Handle different media types with HTML formatting"""
    try:
        if content['media_type'] == 'text':
            await client.send_message(
                chat_id=user_id,
                text=content['text'],
                parse_mode=ParseMode.HTML
            )
        elif content['media_type'] == 'photo':
            await client.send_photo(
                chat_id=user_id,
                photo=content['media_file'],
                caption=content.get('caption', ''),
                parse_mode=ParseMode.HTML
            )
        elif content['media_type'] == 'video':
            await client.send_video(
                chat_id=user_id,
                video=content['media_file'],
                caption=content.get('caption', ''),
                parse_mode=ParseMode.HTML,
                supports_streaming=True
            )
        elif content['media_type'] == 'document':
            await client.send_document(
                chat_id=user_id,
                document=content['media_file'],
                caption=content.get('caption', ''),
                parse_mode=ParseMode.HTML
            )
        # Add more media types as needed
        return True
    except Exception as e:
        logger.error(f"Failed to send {content['media_type']} to {user_id}: {e}")
        failed_users.append(user_id)
        return False