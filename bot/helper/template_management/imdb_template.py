from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.db.user_db import set_user_imdb_template, get_user_imdb_template, remove_user_imdb_template
from bot.permissions.use_bot import user_can_use_bot
from bot.utils.imdb_utils import build_imdb_caption
from pyrogram.enums import ParseMode
# Sample poster URL (You can replace this with any placeholder image URL)
SAMPLE_POSTER_URL = "https://placehold.co/600x400/png?text=Sample+Poster"
async def set_imdb_template_command(client: Client, message: Message):
    """Command to set a user-specific template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    parts = message.text.split(" ", 1)
    text = (
        "**Usage:** `/setimdbtemplate Your IMDB Template or reply to template with the command`\n\n"
        "**Available placeholders:**\n\n"
        "**➤ Basic Info**\n"
        "`{title}`, `{localized_title}`, `{kind}`, `{year}`, `{rating}`, `{votes}`, `{runtime}`, `{genres}`, `{cast}`\n\n"
        "**➤ Crew & Production**\n"
        "`{director}`, `{writer}`, `{producer}`, `{composer}`, `{cinematographer}`, `{music_team}`, `{distributors}`\n\n"
        "**➤ Release & Locale**\n"
        "`{countries}`, `{certificates}`, `{languages}`, `{box_office}`\n\n"
        "**➤ Extras**\n"
        "`{seasons}`, `{plot}`, `{imdb_url}`\n\n"
        "**HTML Formatting Supported:**\n"
        "`<b>Bold</b>`, `<strong>Strong</strong>`, `<i>Italic</i>`, `<em>Emphasis</em>`, `<u>Underline</u>`,\n"
        "`<ins>Inserted</ins>`, `<s>Strikethrough</s>`, `<strike>Strike</strike>`, `<del>Deleted</del>`,\n"
        "`<code>Code</code>`, `<pre>Preformatted</pre>`, `<a href='https://www.imdb.com/'>Link</a>`\n"
    )
    if message.reply_to_message:
        if message.reply_to_message.from_user.id != user_id:
            return await message.reply_text("Not your message")
        custom_message = message.reply_to_message.text or message.reply_to_message.caption
        if not custom_message:
            return await message.reply_text("Replied message has no text/caption to use as template!")
        set_user_imdb_template(user_id, custom_message.strip())
        return await message.reply_text("Custom IMDB template saved from replied message!")

    if len(parts) < 2:
       return await message.reply_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    user_template = parts[1].strip()
    set_user_imdb_template(user_id, user_template)
    await message.reply_text("Your custom IMDB template has been saved!")
    return None


async def get_imdb_template_command(client: Client, message: Message):
    """Command to retrieve a user's template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    user_template = get_user_imdb_template(user_id)
    if user_template:
        await message.reply_text(f"Your current IMDB template:\n\n<code>{user_template}</code>")
        return None
    else:
        await message.reply_text("You have not set a custom IMDB template yet.")
        return None


async def remove_imdb_template_command(client: Client, message: Message):
    """Command to remove a user's template."""
    user_id = message.from_user.id
    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")

    remove_user_imdb_template(user_id)
    await message.reply_text("Your custom IMDB template has been removed.")
    return None


async def preview_imdb_template_command(client: Client, message: Message):
    """Allows the user to preview their current custom template with a sample poster."""
    user_id = message.from_user.id

    if not user_can_use_bot(user_id):
        return await message.reply_text("You are not authorized to use this bot.")


    # Retrieve the user's custom template
    user_template = get_user_imdb_template(user_id)
    if not user_template:
        return await message.reply_text("You have not set a custom IMDB template yet. Use /setimdbtemplate to create one.")

    # Sample drama data for preview
    sample_drama_data = {
        "title": "Autumn’s Promise",
        "localized_title": "Əkim Sözü",  # e.g. in another language
        "kind": "Drama",
        "year": 2021,
        "rating": "8.3",
        "votes": 15432,
        "runtime": "45 min",
        "cast": "Jane Doe, John Smith, Alice Lee",
        "director": "Martin Scorsese",
        "writer": "Sofia Coppola",
        "producer": "Emma Thomas",
        "composer": "Ludwig Göransson",
        "cinematographer": "Roger Deakins",
        "music_team": "Hans Zimmer, John Williams",
        "distributors": "Global Pictures, Indie Films",
        "countries": "USA, Canada",
        "certificates": "PG-13",
        "languages": "English, French",
        "box_office": "$12.5 M",
        "seasons": 2,
        "genres": "🎭 Drama, 🌠 Sci‑Fi, 🥰 Romance",
        "plot": "In a quaint coastal town, two souls bound by fate must confront their pasts to forge a future together.",
        "poster": "https://example.com/poster.jpg",
        "imdb_url": "https://www.imdb.com/title/tt1234567/"
    }

    # Generate the preview caption using the user's template
    preview_caption = build_imdb_caption(user_id, sample_drama_data)

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
    return None