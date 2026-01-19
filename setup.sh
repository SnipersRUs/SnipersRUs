#!/bin/bash

echo "🚀 Setting up Bounty Seeker v4..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ Python 3 and pip3 found"

# Install required packages
echo "📦 Installing required packages..."
pip3 install -r requirements.txt

# Make the main script executable
chmod +x bounty_seeker_v4.py

# Create state file if it doesn't exist
if [ ! -f "state.json" ]; then
    echo "📄 Creating initial state file..."
    python3 -c "
import json
from datetime import datetime, timezone

state = {
    'paper': {
        'balance': 10000.0,
        'trades': [],
        'history': [],
        'stats': {
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0,
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'daily_reset': datetime.now(timezone.utc).isoformat()
        }
    },
    'last_affiliate_post': None,
    'last_sends': {},
    'trade_cache': {}
}

with open('state.json', 'w') as f:
    json.dump(state, f, indent=2)
print('State file created')
"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit config.py and add your Discord webhook URL"
echo "2. Test the scanner: python3 bounty_seeker_v4.py --test"
echo "3. Run continuously: python3 bounty_seeker_v4.py --loop"
echo ""
echo "⚠️  Don't forget to set your Discord webhook in config.py!"
