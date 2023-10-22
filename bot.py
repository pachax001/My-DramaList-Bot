from pyrogram import Client, filters
import html
import logging
import re
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from logging.handlers import RotatingFileHandler


logging.basicConfig(
    filename="botlog.txt",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

log_file_path = "botlog.txt"
file_handler = RotatingFileHandler("bot.log", maxBytes=5 * 1024 * 1024, backupCount=2)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logging.getLogger().addHandler(file_handler)


logging.getLogger().setLevel(logging.INFO)


BOT_TOKEN = "6635179306:AAEzwMCUuFaffjl8NchPmm3LBAPbMm9DG_A"
OWNER_ID = 1940436756

API_ID = "16009913"
API_HASH = "f6a239b37d81c803947bbaf41655350e"
API_URL = "https://kuryana.vercel.app/search/q/{}"
DETAILS_API_URL = "https://kuryana.vercel.app/id/{}"


def filter_dramas(query):
    response = requests.get(API_URL.format(query))
    if response.status_code == 200:
        data = response.json()
        dramas = data.get("results", {}).get("dramas", [])
        return dramas
    else:
        return []


def get_drama_details(slug):
    response = requests.get(DETAILS_API_URL.format(slug))
    if response.status_code == 200:
        data = response.json()
        return data.get("data", {})
    else:
        return None


GENRE_EMOJI = {
    "Action": "🚀",
    "Adult": "🔞",
    "Adventure": "🌋",
    "Animation": "🎠",
    "Biography": "📜",
    "Comedy": "🪗",
    "Crime": "🔪",
    "Documentary": "🎞",
    "Drama": "🎭",
    "Family": "👨‍👩‍👧‍👦",
    "Fantasy": "🫧",
    "Film Noir": "🎯",
    "Game Show": "🎮",
    "History": "🏛",
    "Horror": "🧟",
    "Musical": "🎻",
    "Music": "🎸",
    "Mystery": "🧳",
    "News": "📰",
    "Reality-TV": "🖥",
    "Romance": "🥰",
    "Sci-Fi": "🌠",
    "Short": "📝",
    "Sport": "⛳",
    "Talk-Show": "👨‍🍳",
    "Thriller": "🗡",
    "War": "⚔",
    "Western": "🪩",
}


def load_authorized_users(file_path):
    try:
        with open(file_path, "r") as file:
            return [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:

        return []


def save_authorized_users(file_path, authorized_users):
    with open(file_path, "w") as file:
        for user_id in authorized_users:
            file.write(f"{user_id}\n")


authorized_users = load_authorized_users("authorized_users.txt")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.command("start", prefixes="/"))
async def start_command(client, message):
    user_id = message.from_user.id
    if user_id in authorized_users or user_id == OWNER_ID:
        await message.reply_text(
            "Hi! I can extract details from mydramalist URL or from a search query. For url send /url {mydramalistURL}. For Query send /s {search query}"
        )
    else:
        await message.reply_text("You are not authorized to use this bot.")
        logging.info(f"User {user_id} trying to start the bot")


@app.on_message(filters.command("authorize", prefixes="/") & ~filters.user(OWNER_ID))
async def authorize_command(client, message):
    await message.reply_text("Only the owner can authorize new users.")


@app.on_message(filters.command("unauthorize", prefixes="/") & ~filters.user(OWNER_ID))
async def authorize_command(client, message):
    await message.reply_text("Only the owner can unauthorize current users.")


@app.on_message(filters.command("authorize", prefixes="/") & filters.user(OWNER_ID))
async def authorize_command(client, message):
    try:

        command_parts = message.text.split(" ")
        if len(command_parts) == 2:
            new_user_id = int(command_parts[1])

            if new_user_id in authorized_users:
                await message.reply_text(
                    f"User with ID {new_user_id} is already authorized."
                )
            else:

                authorized_users.append(new_user_id)

                save_authorized_users("authorized_users.txt", authorized_users)

                await message.reply_text(
                    f"User with ID {new_user_id} has been authorized to use the bot."
                )

        else:

            await message.reply_text(
                "Invalid command usage. Correct format: /authorize user_id"
            )

    except ValueError:

        await message.reply_text("Invalid user ID. Please provide a valid user ID.")


@app.on_message(filters.command("unauthorize", prefixes="/") & filters.user(OWNER_ID))
async def unauthorize_command(client, message):
    try:

        command_parts = message.text.split(" ")
        if len(command_parts) == 2:
            user_to_unauthorize = int(command_parts[1])

            if user_to_unauthorize in authorized_users:

                authorized_users.remove(user_to_unauthorize)

                save_authorized_users("authorized_users.txt", authorized_users)

                await message.reply_text(
                    f"User with ID {user_to_unauthorize} has been unauthorized."
                )

            else:

                await message.reply_text(
                    f"User with ID {user_to_unauthorize} is not authorized."
                )

        else:

            await message.reply_text(
                "Invalid command usage. Correct format: /unauthorize user_id"
            )

    except ValueError:

        await message.reply_text("Invalid user ID. Please provide a valid user ID.")


@app.on_message(filters.command("users", prefixes="/") & filters.user(OWNER_ID))
async def users_command(client, message):
    try:

        authorized_users_list = "\n".join(str(user_id) for user_id in authorized_users)

        if len(authorized_users_list.split("\n")) > 30:

            if os.path.exists("authorized_users.txt"):
                with open("authorized_users.txt", "rb") as file:
                    await message.reply_document(document=file)
            else:
                await message.reply_text("Authorized users list file not found.")

        else:

            await message.reply_text("Authorized Users:\n" + authorized_users_list)

    except Exception as e:

        await message.reply_text(f"An error occurred: {e}")


@app.on_message(filters.command("s", prefixes="/"))
async def query_dramas(bot, message):
    try:
        user_id = message.from_user.id
        if message.from_user.id in authorized_users or message.from_user.id == OWNER_ID:
            query = message.text.split(" ", 1)[1]
            dramas = filter_dramas(query)
            logging.info(f"User {user_id} search query : {query}")
            if dramas:
                keyboard = []
                for drama in dramas:

                    callback_data = f"details_{drama['slug']}"
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                f"{drama['title']} ({drama['year']})",
                                callback_data=callback_data,
                            )
                        ]
                    )
                keyboard.append(
                    [InlineKeyboardButton("🚫Close", callback_data="close_search")]
                )
                reply_markup = InlineKeyboardMarkup(keyboard)
                await app.send_message(
                    chat_id=message.chat.id,
                    text="Here are the search results. Click on a drama for more info.",
                    reply_markup=reply_markup,
                )
            else:
                await app.send_message(
                    chat_id=message.chat.id, text="No dramas found with that query."
                )
        else:
            await app.send_message(
                chat_id=message.chat.id, text="Not an authorized user."
            )
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )


@app.on_callback_query(filters.regex(r"^details_"))
async def drama_details(bot, update):
    try:
        user_id = update.from_user.id
        query = update.data.split("_")[1]
        search_results_message = update.message.reply_to_message
        logging.info(
            f"User {user_id} requested details for drama with link: https://mydramalist.com/{query}"
        )
        drama_details = get_drama_details(query)

        if drama_details:
            poster = drama_details.get("poster", None)
            title = drama_details.get("title", "N/A")
            complete_title = drama_details.get("complete_title", "N/A")
            native_title = drama_details["others"].get("native_title", "N/A")
            also_known_as_list = drama_details["others"].get("also_known_as", [])
            also_known_as = (
                ", ".join(also_known_as_list) if also_known_as_list else "N/A"
            )
            rating = drama_details.get("rating", "N/A")
            country = drama_details["details"].get("country", "N/A")
            episodes = drama_details["details"].get("episodes", "N/A")
            aired_date = drama_details["details"].get("aired", "N/A")
            aired_on = drama_details["details"].get("aired_on", "N/A")
            original_network = drama_details["details"].get("original_network", "N/A")
            duration = drama_details["details"].get("duration", "N/A")
            content_rating = drama_details["details"].get("content_rating", "N/A")
            genres = ", ".join(
                f"{GENRE_EMOJI.get(genre, '')} #{genre}".replace("-", "_")
                for genre in drama_details["others"].get("genres", [])
            )
            tags_list = drama_details["others"].get("tags", [])
            if tags_list and tags_list[-1].endswith("(Vote or add tags)"):
                last_tag = tags_list[-1].replace("(Vote or add tags)", "").strip()
                filtered_tags = tags_list[:-1] + [last_tag]
            else:
                filtered_tags = tags_list
            tags = ", ".join(filtered_tags)
            storyline = drama_details.get("synopsis", "N/A")
            drama_link_url = f"https://mydramalist.com/{query}"
            storyline = html.escape(storyline)

            caption = f"<b>{title}</b>\n"
            caption += f"<i>{complete_title}</i>\n"
            caption += f"<b>Native Title:</b> {native_title}\n"
            caption += f"<b>Also Known As:</b> {also_known_as}\n"
            caption += f"<b>Rating ⭐️:</b> {rating}\n"
            caption += f"<b>Country:</b> {country}\n"
            caption += f"<b>Episodes:</b> {episodes}\n"
            caption += f"<b>Aired Date:</b> {aired_date}\n"
            caption += f"<b>Aired On:</b> {aired_on}\n"
            caption += f"<b>Original Network:</b> {original_network}\n"
            caption += f"<b>Duration:</b> {duration}\n"
            caption += f"<b>Content Rating:</b> {content_rating}\n"
            caption += f"<b>Genres:</b> {genres}\n"
            caption += f"<b>Tags:</b> {tags}\n"
            see_more_text = f"<a href='{drama_link_url}'>See more...</a>"
            caption += f"<b>Storyline:</b> {storyline[:100]}{'... '}\n{see_more_text}"

            if poster:
                keyboard = [
                    [InlineKeyboardButton("🚫Close", callback_data="close_search")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await bot.send_photo(
                    chat_id=update.message.chat.id,
                    photo=poster,
                    caption=caption,
                    reply_markup=reply_markup,
                )

            else:
                keyboard = [
                    [InlineKeyboardButton("🚫Close", callback_data="close_search")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await bot.send_message(
                    chat_id=update.message.chat.id,
                    text=caption,
                    reply_markup=reply_markup,
                )
            if search_results_message:
                await search_results_message.delete()

            await update.message.delete()
        else:
            await bot.send_message(
                chat_id=update.message.chat.id, text="Failed to fetch drama details."
            )
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await bot.send_message(
            chat_id=update.message.chat.id,
            text="An error occurred while processing your request. Please try again later.",
        )


@app.on_callback_query(filters.regex(r"^close_search$"))
async def close_search_results(bot, query):
    try:
        await query.answer()
        await query.message.delete()
    except Exception as e:
        logging.error(f"Error closing search results: {e}")


@app.on_message(filters.command("url", prefixes="/"))
async def handle_drama_link(client, message):
    try:
        user_id = message.from_user.id
        if message.from_user.id in authorized_users or message.from_user.id == OWNER_ID:
            drama_link = message.text.split(" ", 1)[1]
            logging.info(
                f"User {user_id} requested drama details for URL: {drama_link}"
            )
            mydramalist_regex = r"https://mydramalist.com/\d+-\S+"
            if re.match(mydramalist_regex, drama_link):
                slug = drama_link.split("/")[-1]
                api_url = f"https://kuryana.vercel.app/id/{slug}"
                response = requests.get(api_url)
                data = response.json()

                title = data["data"]["title"]
                complete_title = data["data"].get("complete_title", "N/A")
                native_title = data["data"]["others"].get("native_title", ["N/A"])[0]
                also_known_as_list = data["data"]["others"].get("also_known_as", [])
                also_known_as = (
                    ", ".join(also_known_as_list) if also_known_as_list else "N/A"
                )
                rating = data["data"].get("rating", "N/A")
                country = data["data"]["details"].get("country", "N/A")
                episodes = data["data"]["details"].get("episodes", "N/A")
                aired_date = data["data"]["details"].get("aired", "N/A")
                aired_on = data["data"]["details"].get("aired_on", "N/A")
                original_network = data["data"]["details"].get(
                    "original_network", "N/A"
                )
                duration = data["data"]["details"].get("duration", "N/A")
                content_rating = data["data"]["details"].get("content_rating", "N/A")
                genres = ", ".join(
                    f"{GENRE_EMOJI.get(genre, '')} #{genre}".replace("-", "_")
                    for genre in data["data"]["others"].get("genres", [])
                )
                tags_list = data["data"]["others"].get("tags", [])
                if tags_list and tags_list[-1].endswith("(Vote or add tags)"):
                    last_tag = tags_list[-1].replace("(Vote or add tags)", "").strip()
                    filtered_tags = tags_list[:-1] + [last_tag]
                else:
                    filtered_tags = tags_list
                tags = ", ".join(filtered_tags)
                storyline = data["data"].get("synopsis", "N/A")

                caption = f"<b>{title}</b>\n"
                caption += f"<i>{complete_title}</i>\n"
                caption += f"<b>Native Title:</b> {native_title}\n"
                caption += f"<b>Also Known As:</b> {also_known_as}\n"
                caption += f"<b>Rating ⭐️:</b> {rating}\n"
                caption += f"<b>Country:</b> {country}\n"
                caption += f"<b>Episodes:</b> {episodes}\n"
                caption += f"<b>Aired Date:</b> {aired_date}\n"
                caption += f"<b>Aired On:</b> {aired_on}\n"
                caption += f"<b>Original Network:</b> {original_network}\n"
                caption += f"<b>Duration:</b> {duration}\n"
                caption += f"<b>Content Rating:</b> {content_rating}\n"
                caption += f"<b>Genres:</b> {genres}\n"
                caption += f"<b>Tags:</b> {tags}\n"
                storyline = html.escape(storyline)

                see_more_text = f"<a href='{drama_link}'>See more...</a>"

                caption += (
                    f"<b>Storyline:</b> {storyline[:100]}{'... '}\n{see_more_text}"
                )
                keyboard = [
                    [InlineKeyboardButton("🚫Close", callback_data="close_search")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await message.reply_photo(
                    photo=data["data"]["poster"],
                    caption=caption,
                    reply_markup=reply_markup,
                )
            else:
                await message.reply_text("Invalid URL.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )


@app.on_message(filters.command("log", prefixes="/"))
async def send_log(client, message):
    try:
        user_id = message.from_user.id
        if user_id == OWNER_ID:

            chat_id = message.chat.id
            log_file_path = os.path.join(os.path.dirname(__file__), "botlog.txt")
            await app.send_document(chat_id, document=log_file_path)
        else:
            await message.reply_text("Only Owner can use this command")
            logging.info(f"User {user_id} trying to access the log")
    except Exception as e:
        logging.error(f"Error processing log file: {e}")
        await message.reply_text("An error occured while processsing the log file.")


if __name__ == "__main__":
    try:
        if os.path.exists(log_file_path):
            logging.shutdown()
            os.remove(log_file_path)
    except Exception as e:
        print(f"Error occurred while deleting log file: {e}")

    app.run()
