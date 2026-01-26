#!/bin/bash
# Start Traditional Markets Bot
# This script starts the bot and keeps it running

cd "$(dirname "$0")"

echo "🚀 Starting Traditional Markets Bot..."
echo "Press Ctrl+C to stop"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the bot
python3 traditional_markets_bot.py
