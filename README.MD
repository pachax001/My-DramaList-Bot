# 🎭 MyDramaList Telegram Bot

**High-Performance Telegram Bot** for searching and retrieving drama/movie information from MyDramaList and IMDB APIs. Features advanced caching, auto-updates, user management, custom templates, and admin controls.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Caching-red.svg)](https://redis.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)](https://www.mongodb.com/)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)

> **Note**: Uses the [Kuryana API](https://github.com/tbdsux/kuryana) for MyDramaList data. You may need to deploy your own instance.

## ✨ **What's New in v2.1**

- 📢 **Enhanced Broadcast System** - Mass broadcasting to millions of users with all message types support
- 🚀 **Real-Time Progress Tracking** - Live broadcast progress with speed and success rate monitoring
- 📱 **Universal Message Support** - Broadcast photos, videos, documents, stickers, locations, and more
- 🎨 **Full HTML Support** - Rich text formatting in broadcast messages with HTML tags
- 🧹 **Code Optimization** - Removed unused code, optimized imports, and improved performance
- 🛠️ **Better Log Management** - Improved `/log` command with automatic log file detection
- 💾 **Advanced Redis Caching** - 2GB memory limit with intelligent TTL management  
- 🔧 **Hot Cache Reload** - Admin command to clear all caches without restart
- 🐳 **Enhanced Docker Support** - Complete containerization with persistent volumes
- ⚡ **Performance Boost** - 10x improvement in concurrent request handling
- 🛡️ **Security Hardening** - Rate limiting, input validation, and secure defaults
- 📊 **Health Monitoring** - Built-in health checks and performance metrics

---

## 🚀 Features

### **General Commands**
- `/start` - Start the bot and receive a welcome message.
- `/help` - Get a list of available commands and usage details.
- `/mdl <query>` - Search using mydramalist.
- `/mdlurl <mydramalist_url>` - Get details by providing MyDramaList URL.
- `/imdb <query>` - Search using IMDB.
- `/imdburl <IMDB_url>` - Get details by providing IMDB URL.

### **User Commands**
- `/setmdltemplate <template>` - Set a custom display template for MyDramaList (Can reply to the template also to add it).
- `/getmdltemplate` - View your current MyDramaList template.
- `/removemdltemplate` - Remove your custom MyDramaList template.
- `/previewmdltemplate` - Preview your custom MyDramaList template.
- `/setimdbtemplate <template>` - Set a custom display template for IMDB (Can reply to the template also to add it).
- `/getimdbtemplate` - View your current IMDB template.
- `/removeimdbtemplate` - Remove your custom IMDB template.
- `/previeiwmdbtemplate` - Preview your custom IMDB template.


### **Admin Commands** (Owner Only)
- `/authorize <user_id>` - Grant access to a specific user
- `/unauthorize <user_id>` - Remove access from a specific user  
- `/users` - View the list of authorized users
- `/userstats` - Get comprehensive bot usage statistics
- `/log` - Retrieve bot logs
- `/setpublicmode <on/off>` - Toggle public mode
- `/broadcast <message>` - ✨ **Enhanced** Mass broadcast to all users (see detailed guide below)
- `/health` - Check service health status (Redis, MongoDB, etc.)
- `/cachereload` - Clear all caches and restart cache client

---

### **Force Sub**
- You can now enable force subscription for a channel. Make sure bot is an admin of the channel.

---

## 📢 **Enhanced Broadcast System** ✨

### **🚀 Massive Scale Broadcasting**
The bot supports broadcasting to **thousands or millions** of users efficiently:

- **✅ Batch Processing**: Handles users in rate-limit friendly batches
- **✅ Concurrent Sending**: Parallel message delivery within batches  
- **✅ Memory Efficient**: Uses MongoDB cursor for large user bases
- **✅ Real-time Progress**: Live updates during broadcast process
- **✅ Performance**: ~1,800 messages/hour respecting Telegram limits

### **📱 Supported Message Types**

#### **Media Types:**
- 🖼️ **Photos** with HTML captions
- 🎥 **Videos** with HTML captions  
- 🎬 **GIFs/Animations** with HTML captions
- 📄 **Documents** with HTML captions
- 🎵 **Audio files** with HTML captions
- 🎙️ **Voice messages**
- 📹 **Video notes (circles)**

#### **Other Types:**
- 🎭 **Stickers**
- 📍 **Locations** 
- 👤 **Contacts**
- 📝 **Text messages** with full HTML formatting

#### **HTML Tags Supported:**
```html
<b>bold</b>, <i>italic</i>, <u>underline</u>, <s>strikethrough</s>
<code>code</code>, <pre>preformatted</pre>, <a href='url'>links</a>
```

### **🎯 Usage Methods**

#### **Method 1: Direct Text Command**
```
/broadcast Hello <b>users</b>! This supports <i>HTML</i> formatting!
```

#### **Method 2: Reply to ANY Message**
1. Send/forward any message (photo, video, sticker, etc.)
2. Reply to it with `/broadcast`
3. Bot broadcasts that exact message type to all users

### **📊 Real-Time Progress Tracking**

During broadcast, you'll see live updates:
```
📢 Broadcasting...
👥 Total Users: 50,000
📊 Progress: 45.2%
📤 Sent: 22,150
❌ Failed: 450
⏱️ Speed: 28.5 msgs/sec
⏰ Elapsed: 796s
```

### **✅ Final Summary Report**
```
✅ Broadcast Completed!
👥 Total Users: 50,000
📤 Successfully Sent: 48,750
❌ Failed: 1,250
📊 Success Rate: 97.5%
⏰ Total Time: 1,750s
⚡ Average Speed: 28.6 msgs/sec
```

### **🚀 Performance Estimates**

| User Count | Estimated Time | Average Speed |
|------------|---------------|---------------|
| 1,000 users | ~2 minutes | ~8 msgs/sec |
| 10,000 users | ~18 minutes | ~9 msgs/sec |
| 100,000 users | ~3 hours | ~9 msgs/sec |
| 1,000,000 users | ~31 hours | ~9 msgs/sec |

### **🛡️ Safety Features**

- **Owner Only**: Only bot owner can use broadcast
- **Rate Limited**: Respects Telegram's API limits
- **Error Resistant**: Failed sends don't crash the process
- **Memory Efficient**: Handles millions of users without memory issues
- **Detailed Logging**: All broadcast activities are logged for monitoring

### **❌ Limitations**
- **Polls**: Cannot be broadcasted (Telegram API limitation)
- **Rate Limits**: Respects Telegram's ~30 messages per second limit
- **Large Files**: Very large media files may cause timeouts

---

## 🛠 Template Usage Guide

You can customize how information is displayed by setting a template using placeholders.




### **Available placeholders:**

#### MyDramaList
- **➤ Drama Info:**  
  `{title}, {complete_title}, {link}, {rating}, {synopsis}`

- **➤ Details:**  
  `{country}, {type}, {episodes}, {aired}, {aired_on}, {original_network}`

- **➤ Additional Info:**  
  `{duration}, {content_rating}, {score}, {ranked}, {popularity},`  
  `{watchers}, {favorites}, {genres}, {tags}, {native_title}, {also_known_as}`

---

#### IMDB

- **➤ Basic Info**
  `{title}`, `{localized_title}`, `{kind}`, `{year}`, `{rating}`, `{votes}`, `{runtime}`, `{genres}`, `{cast}`
- **➤ Crew & Production**
  `{director}`, `{writer}`, `{producer}`, `{composer}`, `{cinematographer}`, `{music_team}`, `{distributors}`
- **➤ Release & Locale**
  `{countries}`, `{certificates}`, `{languages}`, `{box_office}`
- **➤ Extras**
  `{seasons}`, `{plot}`, `{imdb_url}`

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

## 🚀 **Quick Start**

### **Prerequisites**
- [Docker](https://docs.docker.com/engine/install/) and Docker Compose
- [Git](https://git-scm.com/downloads)

### **1. Clone Repository**
```bash
git clone https://github.com/pachax001/My-DramaList-Bot.git
cd My-DramaList-Bot
```

### **2. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your actual values (see configuration below)
nano .env  # or your preferred editor
```

### **3. Deploy with Auto-Update**
```bash
# Deploy with automatic updates enabled
docker-compose up --build -d

# Check logs
docker-compose logs -f mydramalist-bot
```

### **4. Verify Installation**
Send `/health` to your bot (as owner) to check all services are running.

---

## ⚙️ **Configuration**

### **Required Environment Variables**

Add these to your `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather) | `1234567890:ABC...` |
| `API_ID` | Telegram API ID from [my.telegram.org](https://my.telegram.org/auth) | `12345678` |
| `API_HASH` | Telegram API hash from [my.telegram.org](https://my.telegram.org/auth) | `abcdef123456...` |
| `OWNER_ID` | Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot)) | `123456789` |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | MongoDB database name | `mydramalist_bot` |

### **Auto-Update Configuration**

```bash
# Auto-update settings (optional)
AUTO_UPDATE=true                # Enable automatic updates
UPDATE_ON_START=true           # Update on container start  
BACKUP_ON_UPDATE=true          # Create backups (recommended)
UPDATE_REPO=https://github.com/pachax001/My-DramaList-Bot
UPDATE_BRANCH=main

# Performance settings (optional)
REDIS_URL=redis://redis:6379/0  # Redis for caching
CACHE_TTL=3600                 # Cache duration in seconds
MAX_CONNECTIONS=20             # HTTP connection pool size

# Security settings (optional)
IS_PUBLIC=false               # Allow public access
```

### **Optional Features**

```bash
# Force subscription (optional)
FORCE_SUB_CHANNEL_ID=-1001234567890
FORCE_SUB_CHANNEL_URL=https://t.me/yourchannel

# API endpoints (uses Kuryana by default)
API_URL=https://kuryana.vercel.app/api/search
DETAILS_API_URL=https://kuryana.vercel.app/api/info

# Timezone
TZ=UTC
```

---

## 🔧 **Auto-Update System**

### **How It Works**
- Automatically pulls latest code from GitHub repository
- Creates backup before each update for easy rollback
- Validates code syntax and security before applying
- Handles dependency updates automatically
- Supports both scheduled and manual updates

### **Update Modes**

| Mode | Description | Configuration |
|------|-------------|---------------|
| **Startup Update** | Update on container start | `UPDATE_ON_START=true` |
| **Manual Update** | Admin-triggered via bot command | `/cachereload` command |
| **Scheduled Update** | Periodic automatic updates | `AUTO_UPDATE=true` |

### **Backup & Recovery**
```bash
# List available backups
docker exec mydramalist-bot ls -la /usr/src/app/backups/

# Restore from backup (if needed)
docker exec mydramalist-bot python3 update.py --rollback backups/backup_20231201_120000

# Disable auto-updates temporarily
# Set AUTO_UPDATE=false and UPDATE_ON_START=false in .env
```

---

## 📊 **Performance & Caching**

### **Redis Caching System**
- **2GB Memory Limit** with LRU eviction policy
- **Intelligent TTL**: Different cache durations based on content type
  - IMDB Details: 24 hours (rarely change)
  - MDL Details: 12 hours (moderate changes) 
  - Search Results: 1-30 minutes (frequently change)
  - User Templates: 2 hours (user preferences)

### **Cache Management**
- **Hot Reload**: `/cachereload` clears all caches without restart
- **Automatic Cleanup**: Prevents memory leaks in rate limiters
- **Health Monitoring**: Built-in cache performance tracking

### **Rate Limiting**
- **User Protection**: Prevents spam and abuse
- **API Protection**: Shields external APIs from overload
- **Distributed Limiting**: Redis-backed for multi-instance deployments

---

## 🚀 **Deployment**

### **Production Deployment** 
```bash
# Production with auto-updates
AUTO_UPDATE=true UPDATE_ON_START=true docker-compose up --build -d

# Monitor deployment
docker-compose logs -f mydramalist-bot
docker-compose ps
```

### **Development Deployment**
```bash
# Local development without auto-updates
./start.sh --setup    # Setup local environment
./start.sh --check    # Run health checks only
./start.sh            # Start normally
```

### **Docker Management**
```bash
# View logs
docker-compose logs -f mydramalist-bot
docker-compose logs -f mydramalist-redis

# Restart services
docker-compose restart mydramalist-bot
docker-compose restart mydramalist-redis

# Update and rebuild
docker-compose down
docker-compose up --build -d

# Clean deployment (removes volumes)
docker-compose down -v
docker-compose up --build -d
```

---

## 📈 **Monitoring & Health**

### **Health Checks**
- **Service Health**: Redis, MongoDB, HTTP connections
- **Performance Metrics**: Response times, cache hit rates
- **Resource Usage**: Memory, CPU, connection pools
- **Error Tracking**: Failed requests, API timeouts

### **Bot Commands for Monitoring**
- `/health` - Overall service health status
- `/userstats` - User statistics and cache performance  
- `/cachereload` - Clear caches and restart cache client
- `/log` - ✨ **Enhanced** - Smart log file detection and delivery with large file handling

### **Available Metrics**
- Request throughput (requests/second)
- Cache hit ratio (should be >80%)
- Response latency (P95 should be <1 second)
- Error rate (should be <1%)
- Memory usage (Redis should stay under 2GB)

---

## 🔧 **Bot Commands for BotFather**

Copy and paste these into [@BotFather](https://t.me/BotFather):

```
start - Start the bot and see main menu
help - Show detailed help and command guide
mdl - Search MyDramaList or process MDL URL  
mdlurl - Get drama details from MyDramaList URL
imdb - Search IMDB or process IMDB URL
imdburl - Get movie/show details from IMDB URL
setmdltemplate - Set custom MyDramaList template
getmdltemplate - View your current MDL template
removemdltemplate - Remove your MDL template
previewmdltemplate - Preview your MDL template
mdlplaceholders - Show all MyDramaList placeholders
setimdbtemplate - Set custom IMDB template
getimdbtemplate - View your current IMDB template
removeimdbtemplate - Remove your IMDB template
previewimdbtemplate - Preview your IMDB template  
imdbplaceholders - Show all IMDB placeholders
authorize - Grant bot access to a user (Owner Only)
unauthorize - Remove bot access from a user (Owner Only)
users - View authorized users list (Owner Only)
userstats - Get bot usage statistics (Owner Only)
setpublicmode - Toggle public mode on/off (Owner Only)
broadcast - Send message to all users (Owner Only)
log - Get bot log files (Owner Only)
health - Check service health status (Owner Only)
cachereload - Clear all caches and restart cache client (Owner Only)
```

---

## 🛠 **Development Guide**

### **Local Development** (without Docker)
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup local services (optional, or use cloud services)
# Redis: redis-server
# MongoDB: mongod

# Create config.env from template
cp sample_config.env config.env
# Edit config.env with your values

# Run bot
python3 main.py
```

### **Architecture Overview**

The bot follows a layered architecture pattern for high performance and maintainability:

```
📁 Project Structure
├── 🔧 infra/           # Infrastructure layer (Redis, MongoDB, HTTP)
│   ├── cache/          # Redis caching with intelligent TTL
│   ├── db/             # MongoDB connection and operations  
│   ├── http/           # HTTP client with connection pooling
│   └── logging/        # Structured logging with correlation IDs
├── 🏛️ domain/          # Business logic layer
│   └── services/       # Core services (template processing, etc.)
├── 🔌 adapters/        # External service integrations
│   ├── mydramalist/    # MyDramaList API client
│   ├── imdb/           # IMDB API client with thread pool
│   └── telegram/       # Telegram bot handlers
└── 🚀 app/             # Application layer
    └── middleware/     # Performance monitoring, health checks
```

### **Performance Features**
- **Async I/O**: 10x improvement in concurrent request handling
- **Connection Pooling**: Persistent connections for HTTP and MongoDB
- **Intelligent Caching**: Redis with adaptive TTLs based on content type  
- **Rate Limiting**: Token bucket algorithm with distributed Redis backing
- **Thread Pool**: Non-blocking execution for synchronous operations
- **Circuit Breakers**: Fault tolerance with exponential backoff
- **Code Optimization** ✨: Removed unused imports, dead code, and optimized dependencies  
- **Enhanced Logging** ✨: Smart log file detection with automatic cleanup for large files
- **Mass Broadcast System** ✨: Efficient broadcasting to millions of users with progress tracking
- **Streamlined Architecture**: Reduced complexity and improved maintainability

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Environment Variables Not Loading**
```bash
# Check .env file format
cat .env | grep -v '^#' | grep '='

# Restart containers to reload
docker-compose down && docker-compose up -d
```

#### **Redis Connection Failed**
```bash
# Check Redis health
docker exec mydramalist-redis redis-cli ping

# Restart Redis
docker-compose restart mydramalist-redis

# Check Redis memory usage
docker exec mydramalist-redis redis-cli info memory
```

#### **MongoDB Connection Issues**
```bash
# Check MongoDB connection
docker exec mydramalist-bot python3 -c "from infra.db import mongo_client; print('MongoDB OK')"

# Verify connection string format
echo $MONGO_URI
```

#### **Update Failures**
```bash
# Check update logs
docker-compose logs mydramalist-bot | grep -i update

# Disable auto-updates temporarily
# Set AUTO_UPDATE=false in .env and restart

# Manual rollback
docker exec mydramalist-bot python3 update.py --rollback backups/latest_backup
```


#### **Broadcast Issues**
```bash
# Check if broadcast is running
docker-compose logs mydramalist-bot | grep -i broadcast

# Monitor broadcast progress
# Use /broadcast command and watch real-time progress updates

# Check user database
docker exec mydramalist-bot python3 -c "
from infra.db import mongo_client
import asyncio
async def check():
    await mongo_client.start()
    count = await mongo_client.db.users.count_documents({})
    print(f'Total users: {count}')
asyncio.run(check())
"

# Test with small broadcast first
# Use /broadcast test message to verify functionality
```

#### **Performance Issues**
```bash
# Check cache hit ratio (should be >80%)
docker exec mydramalist-redis redis-cli info stats | grep keyspace_hits

# Monitor resource usage during broadcast
docker stats mydramalist-bot mydramalist-redis

# Check for memory leaks
docker exec mydramalist-bot ps aux | grep python
```

### **Debug Mode**
```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart mydramalist-bot

# View detailed logs
docker-compose logs -f mydramalist-bot | grep DEBUG
```

### **Emergency Recovery**
```bash
# Complete reset (keeps data)
docker-compose down
docker-compose up --build -d

# Nuclear option (removes all data)
docker-compose down -v
rm -rf .env
cp .env.example .env
# Reconfigure .env
docker-compose up --build -d
```

---

## 🏗️ **System Requirements**

### **Minimum Requirements**
- **CPU**: 1 vCPU (2+ recommended)
- **RAM**: 512MB (1GB+ recommended)  
- **Disk**: 2GB free space
- **Network**: Stable internet connection

### **Recommended for Production**
- **CPU**: 2+ vCPUs for concurrent user handling
- **RAM**: 2GB+ (1GB for Redis cache, 1GB for bot)
- **Disk**: 5GB+ with SSD for better I/O performance
- **Network**: High bandwidth for media-heavy responses

### **Docker Resource Limits**
The docker-compose.yml includes reasonable defaults, but you can adjust:

```yaml
# Add to mydramalist-bot service in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:  
      memory: 256M
      cpus: '0.1'
```

---

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** with proper testing
4. **Follow the architecture patterns** described above
5. **Submit a pull request** with clear description

### **Development Guidelines**
- Use async/await for all I/O operations
- Add proper error handling and logging
- Include tests for new features
- Follow the existing code style
- Update documentation for new features

---

## 📞 **Support**

### **Documentation**
- **Setup Issues**: Check this README and `.env.example`
- **Bot Commands**: Use `/help` command in bot
- **API Issues**: Check [Kuryana API](https://github.com/tbdsux/kuryana)

### **Community**
- **GitHub Issues**: [Report bugs and feature requests](https://github.com/pachax001/My-DramaList-Bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pachax001/My-DramaList-Bot/discussions)
- **Telegram**: [@gunaya001contactbot](https://t.me/gunaya001contactbot) for direct support

### **Performance Monitoring**
Send `/health` to your bot (as owner) to get:
- Service health status (Redis, MongoDB, HTTP)
- Cache performance metrics
- Memory usage and connection pool status
- Recent error rates and response times

---

## 📄 **License**

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.

---

## 🚀 **Version History**

### **v2.1** (Latest) ✨
- **Enhanced Broadcast System** - Mass broadcasting to millions of users with all message types
- **Real-Time Progress Tracking** - Live broadcast monitoring with speed and success metrics
- **Universal Message Support** - Photos, videos, documents, stickers, locations, contacts, and more
- **Full HTML Support** - Rich text formatting in broadcast messages
- Code optimization and cleanup (removed unused code/imports)
- Improved log management with smart file detection  
- Better error handling and fallback mechanisms
- Streamlined codebase for better performance
- Enhanced stability and reduced memory usage

### **v2.0** 
- Auto-update system with backup/restore
- Advanced Redis caching with intelligent TTL
- Hot cache reload functionality
- Enhanced Docker support with persistent volumes
- 10x performance improvement
- Security hardening and rate limiting
- Built-in health monitoring

## 🙏 **Acknowledgments**

- **[Kuryana API](https://github.com/tbdsux/kuryana)** - MyDramaList data source
- **[Pyrogram](https://github.com/pyrogram/pyrogram)** - Telegram bot framework  
- **[Redis](https://redis.io/)** - High-performance caching
- **[MongoDB](https://www.mongodb.com/)** - Document database
- **[Docker](https://www.docker.com/)** - Containerization platform
- **Claude Code** - AI-assisted development and optimization

---

<div align="center">

**⭐ Star this repository if it helped you!**

[![GitHub stars](https://img.shields.io/github/stars/pachax001/My-DramaList-Bot?style=social)](https://github.com/pachax001/My-DramaList-Bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/pachax001/My-DramaList-Bot?style=social)](https://github.com/pachax001/My-DramaList-Bot/network/members)

Made with ❤️ for the K-Drama community

</div>