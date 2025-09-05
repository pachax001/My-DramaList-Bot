python3 -c "import uvloop" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ uvloop detected - running in high performance mode"
else
    echo "⚠️ uvloop not found - installing..."
    pip install uvloop
fi

if python3 -O update.py; then
  echo "Update step completed."
else
  echo "Update step failed (continuing anyway)..." >&2
fi

# Optimize kernel network settings (ignore failures in containers)
echo 65536 > /proc/sys/net/core/somaxconn 2>/dev/null || true

# Run the bot
exec python3 -O main.py # -O flag for optimizations