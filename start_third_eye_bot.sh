#!/bin/bash
# Third Eye Bot Startup Script

cd /Users/bishop/Documents/GitHub/SnipersRUs

echo "🤖 Starting Third Eye Sentiment Bot..."

# Check if already running
if pgrep -f "mind_bot.py" > /dev/null; then
    echo "⚠️  Bot is already running!"
    echo "Use 'python3 monitor_mind_bot.py --restart' to restart"
    exit 1
fi

# Start the bot
nohup python3 mind_bot.py > mind_bot.log 2>&1 &

# Wait a moment and check if it started
sleep 2
if pgrep -f "mind_bot.py" > /dev/null; then
    echo "✅ Third Eye Bot started successfully!"
    echo "📊 Monitor with: python3 monitor_mind_bot.py --status"
    echo "📝 Logs: tail -f mind_bot.log"
else
    echo "❌ Failed to start bot. Check mind_bot.log for errors."
    exit 1
fi























