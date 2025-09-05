# 🚀 MyDramaList Bot - Auto-Update Deployment Guide

## 📋 **Quick Start**

### **1. Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit with your actual values
nano .env  # or your preferred editor
```

### **2. Docker Deployment (Recommended)**
```bash
# Deploy with auto-update enabled
docker-compose up --build -d

# Check logs
docker-compose logs -f mydramalist-bot
```

### **3. Local Development**
```bash
# Install and run with auto-update
./start.sh --update
```

## 🔧 **Environment Configuration**

### **Required Variables**
Put these in your `.env` file:

```bash
# Telegram Configuration
BOT_TOKEN=your_bot_token_from_botfather
API_ID=your_api_id
API_HASH=your_api_hash
OWNER_ID=your_telegram_user_id

# Database
MONGO_URI=mongodb://localhost:27017/mydramalist_bot
```

### **Auto-Update Configuration**
```bash
# Enable auto-updates
AUTO_UPDATE=true
UPDATE_ON_START=true
BACKUP_ON_UPDATE=true

# Repository settings
UPDATE_REPO=https://github.com/pachax001/My-DramaList-Bot
UPDATE_BRANCH=main
```

## 🐳 **Docker Compose Deployment**

### **Complete docker-compose.yml Features**
- ✅ **Automatic environment loading** from `.env`
- ✅ **Persistent volumes** for backups, logs, and data
- ✅ **Redis caching** with 2GB memory limit
- ✅ **Health checks** for both services
- ✅ **Auto-update support** with git integration
- ✅ **Security hardening** with non-root user

### **Deployment Commands**

#### **Initial Deployment**
```bash
# Clone repository
git clone https://github.com/pachax001/My-DramaList-Bot.git
cd My-DramaList-Bot

# Setup environment
cp .env.example .env
# Edit .env with your values

# Deploy
docker-compose up --build -d
```

#### **Update Deployment**
```bash
# Method 1: Auto-update (if enabled)
docker-compose restart mydramalist-bot  # Updates automatically on start

# Method 2: Manual update
docker-compose down
git pull origin main
docker-compose up --build -d

# Method 3: Force update via bot command
# Send /cachereload to bot as owner
```

## ⚙️ **Auto-Update Modes**

### **Mode 1: Auto-Update on Start**
```bash
# In .env
AUTO_UPDATE=false
UPDATE_ON_START=true  # Updates every container start
```

### **Mode 2: Continuous Auto-Update**
```bash
# In .env  
AUTO_UPDATE=true      # Enables periodic updates
UPDATE_ON_START=true  # Also updates on start
```

### **Mode 3: Manual Update Only**
```bash
# In .env
AUTO_UPDATE=false
UPDATE_ON_START=false  # Manual updates only
```

## 💾 **Backup System**

### **Automatic Backups**
- Created before each update when `BACKUP_ON_UPDATE=true`
- Stored in persistent volume `bot-backups`
- Timestamped format: `backup_YYYYMMDD_HHMMSS`

### **Backup Management**
```bash
# List backups
docker exec mydramalist-bot ls -la /usr/src/app/backups/

# Restore from backup
docker exec mydramalist-bot python3 update.py --rollback backups/backup_20231201_120000
```

## 🔄 **Update Workflow**

### **Automated Update Process**
1. **Backup Creation** - Current installation backed up
2. **Repository Clone** - Latest code fetched from GitHub
3. **Validation** - Security and syntax checks
4. **File Replacement** - Code files updated
5. **Dependency Check** - Requirements reinstalled if needed
6. **Service Restart** - Container restarted (if needed)

### **Update Triggers**
- 🔄 **Container Start**: `UPDATE_ON_START=true`
- ⚡ **Bot Command**: `/cachereload` (owner only)
- 🔧 **Manual**: `./start.sh --update`

## 📊 **Monitoring & Health Checks**

### **Service Health**
```bash
# Check service status
docker-compose ps

# View health status
docker inspect mydramalist-bot | grep Health -A 10
```

### **Bot Commands** (Owner Only)
- `/health` - Service health status
- `/userstats` - User and cache statistics  
- `/cachereload` - Clear caches and check for updates
- `/log` - Download log files

### **Log Monitoring**
```bash
# Bot logs
docker-compose logs -f mydramalist-bot

# Redis logs  
docker-compose logs -f mydramalist-redis

# Live log monitoring
docker exec mydramalist-bot tail -f logs/bot_*.log
```

## 🛡️ **Security Features**

### **Container Security**
- ✅ **Non-root user** execution
- ✅ **Read-only** Redis configuration
- ✅ **Isolated network** for services
- ✅ **Resource limits** (Redis 2GB memory)

### **Update Security**
- ✅ **Repository validation** (HTTPS only)
- ✅ **Code validation** (syntax checks)
- ✅ **Backup system** (automatic rollback)
- ✅ **Permission checks** (owner-only updates)

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Environment Variables Not Loaded**
```bash
# Check .env file exists and has correct format
ls -la .env
cat .env

# Restart containers to reload environment
docker-compose down && docker-compose up -d
```

#### **Update Failures**
```bash
# Check update logs
docker-compose logs mydramalist-bot | grep -i update

# Manual rollback
docker exec mydramalist-bot python3 update.py --rollback backups/latest_backup

# Skip updates temporarily
docker-compose down
# Set UPDATE_ON_START=false in .env
docker-compose up -d
```

#### **Redis Connection Issues**
```bash
# Check Redis health
docker exec mydramalist-redis redis-cli ping

# Restart Redis
docker-compose restart mydramalist-redis

# Check Redis memory
docker exec mydramalist-redis redis-cli info memory
```

#### **Permission Issues**
```bash
# Fix container permissions
docker exec --user root mydramalist-bot chown -R botuser:botuser /usr/src/app

# Rebuild with fresh volumes
docker-compose down -v
docker-compose up --build -d
```

## 📈 **Performance Tuning**

### **Redis Configuration**
- **Memory Limit**: 2GB with LRU eviction
- **Persistence**: Optimized for caching workloads
- **Connections**: Up to 1000 concurrent clients

### **Bot Performance**
- **Connection Pooling**: HTTP clients with connection reuse
- **Caching Strategy**: Multi-tier with adaptive TTLs
- **Rate Limiting**: Protection against API abuse

### **Container Resources**
```yaml
# Add to docker-compose.yml under mydramalist-bot service
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.1'
```

## 🚨 **Emergency Procedures**

### **Disable Auto-Updates**
```bash
# Emergency stop auto-updates
docker exec mydramalist-bot touch /usr/src/app/.no_auto_update

# Or via environment
docker-compose down
# Set AUTO_UPDATE=false and UPDATE_ON_START=false in .env
docker-compose up -d
```

### **Manual Recovery**
```bash
# Complete reset
docker-compose down -v  # Removes all volumes
git checkout HEAD~1     # Revert to previous commit
docker-compose up --build -d

# Partial reset (keep data)
docker-compose down
docker-compose up --build -d
```

## ✅ **Deployment Checklist**

- [ ] **Environment**: `.env` file created with all required variables
- [ ] **Repository**: Set correct `UPDATE_REPO` URL in `.env`
- [ ] **Credentials**: Valid Telegram bot token and API credentials
- [ ] **Database**: MongoDB accessible and configured
- [ ] **Permissions**: Bot owner ID correctly set
- [ ] **Updates**: Auto-update mode chosen and configured
- [ ] **Backups**: `BACKUP_ON_UPDATE=true` for safety
- [ ] **Monitoring**: Health checks and logging configured
- [ ] **Security**: Redis and container security verified

## 📞 **Support**

- 📖 **Documentation**: Check this file and `CLAUDE.md`
- 🐛 **Issues**: Report at [GitHub Issues](https://github.com/pachax001/My-DramaList-Bot/issues)
- 💬 **Bot Commands**: Use `/help` for command list
- 🔍 **Logs**: Check container logs for detailed error information