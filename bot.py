from pyrogram import Client, filters
import requests
import html
import logging
import re
import os

logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Fill these variables
API_ID = ""
API_HASH = ""
BOT_TOKEN = ""
OWNER_ID = 

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
            "Hi! I can extract details from MyDramalist. Please send the MyDramalist URL."
        )
    else:
        await message.reply_text("You are not authorized to use this bot.")


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


@app.on_message()
async def handle_drama_link(client, message):
    try:

        if message.from_user.id in authorized_users or message.from_user.id == OWNER_ID:
            drama_link = message.text
            mydramalist_regex = r"https://mydramalist.com/\d+-\S+"
            if re.match(mydramalist_regex, drama_link):

                slug = drama_link.split("/")[-1]

                api_url = f"https://kuryana.vercel.app/id/{slug}"
                response = requests.get(api_url)

                data = response.json()

                title = data["data"]["title"]
                complete_title = data["data"]["complete_title"]
                native_title = data["data"]["others"]["native_title"][0]
                also_known_as_list = data["data"]["others"]["also_known_as"]
                also_known_as = (
                    ", ".join(also_known_as_list) if also_known_as_list else "N/A"
                )
                rating = data["data"]["rating"]
                country = data["data"]["details"]["country"]
                episodes = data["data"]["details"]["episodes"]
                aired_date = data["data"]["details"]["aired"]
                aired_on = data["data"]["details"]["aired_on"]
                original_network = data["data"]["details"]["original_network"]
                duration = data["data"]["details"]["duration"]
                content_rating = data["data"]["details"]["content_rating"]
                genres = ", ".join(
                    f"{GENRE_EMOJI.get(genre, '')} #{genre}"
                    for genre in data["data"]["others"]["genres"]
                )
                tags_list = data["data"]["others"]["tags"]

                if tags_list and tags_list[-1].endswith("(Vote or add tags)"):
                    last_tag = tags_list[-1].replace("(Vote or add tags)", "").strip()
                    filtered_tags = tags_list[:-1] + [last_tag]
                else:
                    filtered_tags = tags_list

                tags = ", ".join(filtered_tags)
                storyline = data["data"]["synopsis"]

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

                await message.reply_photo(photo=data["data"]["poster"], caption=caption)
            else:
                await message.reply_text("Invalid URL.")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )


app.run()
