#!/bin/bash
# Run bot in background with nohup
cd "$(dirname "$0")"

# Kill any existing instances
pkill -f "traditional_markets_bot.py" 2>/dev/null

# Start in background with nohup
nohup python3 traditional_markets_bot.py > bot_output.log 2>&1 &

echo "✅ Bot started in background"
echo "PID: $!"
echo "Logs: bot_output.log"
echo ""
echo "To check status: tail -f bot_output.log"
echo "To stop: pkill -f traditional_markets_bot.py"
