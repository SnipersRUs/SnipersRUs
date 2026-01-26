#!/bin/bash
# Run the Piv X Signal Bot

echo "🚀 Starting Piv X Signal Bot..."
echo "Scanning: BTC, SOL, ETH"
echo "Interval: Every hour"
echo ""

cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check for required packages
python3 -c "import ccxt, pandas, numpy, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install ccxt pandas numpy requests
fi

# Run the bot
python3 pivx_signal_bot.py
