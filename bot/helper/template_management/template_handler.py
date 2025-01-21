# bot/helper/template/template_handler.py

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.user_db import set_user_template, get_user_template, remove_user_template
from bot.permissions.use_bot import user_can_use_bot
from bot.utils.drama_utils import build_drama_caption
from pyrogram.enums import ParseMode
# Sample poster URL (You can replace this with any placeholder image URL)
SAMPLE_POSTER_URL = "https://placehold.co/600x400/png?text=Sample+Poster"
async def set_template_command(client: Client, message: Message):
    """Command to set a user-specific template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    parts = message.text.split(" ", 1)
    text = (
        "**Usage:** `/settemplate Your Template`\n\n"
        "**Available placeholders:**\n\n"
        "**➤ Drama Info**\n"
        "`{title}`, `{complete_title}`, `{link}`, `{rating}`, `{synopsis}`\n\n"
        "**➤ Details**\n"
        "`{country}`, `{type}`, `{episodes}`, `{aired}`, `{aired_on}`, `{original_network}`\n\n"
        "**➤ Additional Info**\n"
        "`{duration}`, `{content_rating}`, `{score}`, `{ranked}`, `{popularity}`,\n"
        "`{watchers}`, `{favorites}`, `{genres}`, `{tags}`, `{native_title}`, `{also_known_as}`\n\n"
        "**HTML Formatting Supported:**\n"
        "`<b>Bold</b>`, `<strong>Strong</strong>`, `<i>Italic</i>`, `<em>Emphasis</em>`, `<u>Underline</u>`,\n"
        "`<ins>Inserted</ins>`, `<s>Strikethrough</s>`, `<strike>Strike</strike>`, `<del>Deleted</del>`,\n"
        "`<code>Code</code>`, `<pre>Preformatted</pre>`, `<a href='https://mydramalist.com/'>Link</a>`\n"
    )


    if len(parts) < 2:
       return await message.reply_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )

    user_template = parts[1].strip()
    set_user_template(user_id, user_template)
    await message.reply_text("Your custom template has been saved!")


async def get_template_command(client: Client, message: Message):
    """Command to retrieve a user's template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    user_template = get_user_template(user_id)
    if user_template:
        await message.reply_text(f"Your current template:\n\n<code>{user_template}</code>")
    else:
        await message.reply_text("You have not set a custom template yet.")


async def remove_template_command(client: Client, message: Message):
    """Command to remove a user's template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    remove_user_template(user_id)
    await message.reply_text("Your custom template has been removed.")



async def preview_template_command(client: Client, message: Message):
    """Allows the user to preview their current custom template with a sample poster."""
    user_id = message.from_user.id

    # Retrieve the user's custom template
    user_template = get_user_template(user_id)
    if not user_template:
        return await message.reply_text("You have not set a custom template yet. Use /settemplate to create one.")

    # Sample drama data for preview
    sample_drama_data = {
        "title": "Sample Drama",
        "complete_title": "Sample Drama Full Title",
        "rating": "9.0",
        "others": {
            "native_title": ["샘플 드라마"],
            "also_known_as": ["Test Show"],
            "genres": ["Drama", "Action"],
            "tags": ["Revenge", "Suspense"],
        },
        "details": {
            "country": "South Korea",
            "episodes": "16",
            "aired": "2023-01-01",
            "aired_on": "Monday",
            "original_network": "Netflix",
            "duration": "60 min",
            "content_rating": "PG-13",
        },
        "synopsis": "This is a sample synopsis to demonstrate how your custom template will look in real usage.",
    }

    # Generate the preview caption using the user's template
    preview_caption = build_drama_caption(user_id, sample_drama_data, "sample-drama")

    # Prepare an inline keyboard to give the user more options
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🚫 Close Preview", callback_data="close_search")]
        ]
    )

    # Send the sample poster with caption
    await message.reply_photo(
        photo=SAMPLE_POSTER_URL,
        caption=preview_caption,
        reply_markup=markup
    )