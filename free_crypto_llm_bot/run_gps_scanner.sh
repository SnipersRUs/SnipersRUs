#!/bin/bash
# GPS Scanner Bot - Quick Start Script

echo "🚀 Starting GPS Scanner Bot..."
echo "📊 Scanning for coins near Previous Week GPS levels"
echo "⏰ Scan interval: 15 minutes"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the scanner
python3 gps_scanner_bot.py


