# MyDramaList Bot


#### This Bot can extract drama details from  [MyDramaList](https://mydramalist.com/) url.
#### Send any valid Mydramalist link and the bot gives you the drama details as a post.

## Installation
### Prerequisites
Install python3.x in your system
### Deploy in your vps(Linux)

1. Clone the repo and change directory to My-DramaList-Bot
```
git clone https://github.com/pachax001/My-DramaList-Bot.git  && cd My-DramaList-Bot
```
2. Fill the variables in [bot.py](https://github.com/pachax001/My-DramaList-Bot/blob/9ddb724698c77fbbdb39f2f917b20835d84fa2dd/bot.py#L13C1-L13C1)
<br> [Click here](https://github.com/pachax001/My-DramaList-Bot/blob/main/README.md#configs) for more info on config. </br>

3. Run the following command in terminal. Make sure you are in clone directory.
```
pip install -r requirements.txt
```
4. After filling and saving bot.py type this command in terminal and press enter.
```
python3 bot.py
```
To run the bot even after closing session use [TMUX](https://github.com/tmux/tmux/wiki)
## Configs

* BOT_TOKEN     - Get bot token from @BotFather

* APP_ID        - From my.telegram.org (or @UseTGXBot)

* API_HASH      - From my.telegram.org (or @UseTGXBot)

* OWNER_ID  - Your telegram ID
### 🤖 ***Bot Commands***
####Set these commands from [@BotFather](https://t.me/BotFather)
```
start - Start the bot
authorize - Authorize new user.
unauthorize - Unauthorize an exsisting user.
users - To see the ids od authorized users.
```
## 🏅 **Credits**
|<img width="80" src="https://avatars.githubusercontent.com/u/37932956">|<img width="80" src="https://avatars.githubusercontent.com/u/34474300">|

|[`Joshue Abance`](https://github.com/tbdsux)|[`Pyrogram`](https://github.com/pyrogram)|
<br>|Creator of MDL API|Telegram Bot Framework|</br>

