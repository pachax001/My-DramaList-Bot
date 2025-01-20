# MyDramaList Telegram Bot

MyDramaList Telegram Bot is a powerful bot that allows users to search for dramas, retrieve details using MyDramaList URLs, and customize the display of drama information using templates. It supports user management, template customization, admin control, and public mode toggling.

For the mydramalist API this bot uses [this custom API](https://github.com/tbdsux/kuryana). Might need to deploy your own API using this for bot to work.

---

## 🚀 Features

### **General Commands**
- `/start` - Start the bot and receive a welcome message.
- `/help` - Get a list of available commands and usage details.
- `/s <query>` - Search for a drama by title.
- `/url <mydramalist_url>` - Get drama details by providing a MyDramaList URL.

### **User Commands**
- `/settemplate <template>` - Set a custom display template.
- `/gettemplate` - View your current template.
- `/removetemplate` - Remove your custom template.
- `/previewtemplate` - Preview your custom template.

### **Inline Search**
- Search dramas inline in any chat using `@mydramalist001bot <query>`.
- Example: `@mydramalist001bot Vincenzo`.

### **Admin Commands**
- `/authorize <user_id>` - Grant access to a specific user.
- `/unauthorize <user_id>` - Remove access from a specific user.
- `/users` - View the list of authorized users.
- `/log` - Retrieve bot logs.
- `/setpublicmode` - Toggle public mode on/off.
- `/broadcast <message>` - Send a message to all users.

---

## 🛠 Template Usage Guide

You can customize how drama information is displayed by setting a template using placeholders.

### **Usage:**

`/settemplate Your Template`


### **Available placeholders:**

- **➤ Drama Info:**  
  `{title}, {complete_title}, {link}, {rating}, {synopsis}`

- **➤ Details:**  
  `{country}, {type}, {episodes}, {aired}, {aired_on}, {original_network}`

- **➤ Additional Info:**  
  `{duration}, {content_rating}, {score}, {ranked}, {popularity},`  
  `{watchers}, {favorites}, {genres}, {tags}, {native_title}, {also_known_as}`

---

### **Supported HTML Formatting:**

`<b>Bold</b>, <strong>Strong</strong>, <i>Italic</i>, <em>Emphasis</em>, <u>Underline</u>, <ins>Inserted</ins>, <s>Strikethrough</s>, <strike>Strike</strike>, <del>Deleted</del>, <code>Code</code>, <pre>Preformatted</pre>, <a href='https://mydramalist.com/'>Link</a>`


---

## 🔓 Public Mode

Public mode allows or restricts access to the bot for all users. Admins can enable or disable public access using the following command:

`/setpublicmode on/off`


- **Enabled:** Anyone can use the bot.  
- **Disabled:** Only authorized users can access the bot.

---

## 🏗️ Installation Guide

### **1. Prerequisites**
Ensure you have the following installed on your system:
- [Docker](https://docs.docker.com/engine/install/ubuntu/)


---

### **2. Clone the Repository**
```
git clone https://github.com/yourusername/mydramalist-bot.git
cd mydramalist-bot
```
### **3. Configure the Bot**
Copy content of sample_config.env to config.env

```
cp sample_config.env config.env
```

#### Variables in config.env


`BOT_TOKEN `  Get this from [@BotFather](https://t.me/BotFather) <br>
`OWNER_ID`    Your telegram id<br>
`API_ID`      Get this from [my.telegram.org](https://my.telegram.org/auth) <br>
`API_HASH`    Get this from [my.telegram.org](https://my.telegram.org/auth) <br>
`IS_PUBLIC`   Boolean Value.true or false. If set to true anyone can use the bot. Can be changed using `/setpublicmode on/off` while bot running. A status message will be sent to all the users of the bot. <br>
`MONGO_URI`   MongoDB URL. Generate it from [mongodb.com](https://www.mongodb.com/). For generation instructions [click here.](https://github.com/pachax001/My-Asian-Tv-Dramacool-Telegram-bot#-generate-mongodb-database) <br>
`DB_NAME`     MongoDB name. <br>
`API_URL`     Custom deployed API url from [https://github.com/tbdsux/kuryana](https://github.com/tbdsux/kuryana). Default value is `https://kuryana.vercel.app/search/q/{}`. <br>
`DETAILS_API_URL`  Custom deployed API url from [https://github.com/tbdsux/kuryana](https://github.com/tbdsux/kuryana). Default value is `https://kuryana.vercel.app/id/{}`. <br>

### **4. Build and Run the Bot**

```
docker-compose up --build -d
```

### 🛠 Development Guide

### **Running Locally Without Docker**

1. Install dependencies manually
```
python3 -m venv venv
source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
pip install -r requirements.txt
```
2. Run the bot manually:
```
python3 main.py
```
### **🚀 Deployment**
The bot will automatically restart using Docker if the server reboots or if an error occurs.
Use the following command to stop the bot manually:
```
docker-compose down
```

### **👤 Contact**
For any issues or questions, contact the bot owner:

[Telegram: Bot Owner](https://t.me/gunaya001)

### ⚠️ License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.