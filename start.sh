#!/bin/bash

# Check if uvloop is available
python3 -c "import uvloop" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ uvloop detected - running in high performance mode"
else
    echo "⚠️ uvloop not available (continuing without it)"
fi


# Optimize kernel network settings (ignore failures in containers)
echo 65536 > /proc/sys/net/core/somaxconn 2>/dev/null || echo "⚠️ Cannot modify kernel settings in container (expected)"

if python3 -O update.py; then
  echo "Update step completed."
else
  echo "Update step failed (continuing anyway)..." >&2
fi

# Run the bot with optimizations
echo "🚀 Starting MyDramaList Bot..."
exec python3 -O main.py