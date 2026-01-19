# 🚀 Bounty Seeker v4 - Quick Start Guide

## Step 1: Setup (One-time)

### Option A: Using the setup script (Recommended)
```bash
./setup.sh
```

### Option B: Manual setup
```bash
# Install dependencies
pip3 install -r requirements.txt

# Make script executable
chmod +x bounty_seeker_v4.py
```

## Step 2: Configure Discord Webhook

1. Open `config.py` in Cursor
2. Replace `YOUR_DISCORD_WEBHOOK_URL_HERE` with your actual Discord webhook URL
3. Save the file

### How to get Discord webhook:
1. Go to your Discord server
2. Right-click on the channel where you want notifications
3. Select "Edit Channel" → "Integrations" → "Webhooks"
4. Click "Create Webhook"
5. Copy the webhook URL

## Step 3: Test the Scanner

### Single scan test:
```bash
python3 bounty_seeker_v4.py --test
```

### Run continuously (every hour):
```bash
python3 bounty_seeker_v4.py --loop
```

## Step 4: Monitor Results

- Check your Discord channel for trade signals
- Each trade includes:
  - Setup reasoning
  - Entry/stop levels
  - Risk management details
  - Confidence score

## 📊 What the Scanner Does

- **Scans**: Bybit, Bitget, MEXC exchanges
- **Finds**: Reversal setups, momentum breakouts
- **Filters**: VWAP confluence, volume confirmation
- **Delivers**: Top 3 trades + 3 watchlist items per hour
- **Risk**: $300 per trade (3% of $10k account)

## 🛠️ Troubleshooting

### If you get "No Discord webhook configured":
- Make sure you've updated `config.py` with your webhook URL
- Check that the webhook URL is correct

### If you get import errors:
- Run: `pip3 install -r requirements.txt`
- Make sure you're using Python 3.8+

### If the scanner doesn't find trades:
- This is normal - it only shows high-quality setups
- Check the watchlist for building momentum

## 📈 Expected Performance

- **Signal Quality**: High (VWAP confluence required)
- **Trade Frequency**: 0-3 trades per hour
- **Risk Management**: 3% per trade, auto-close at 5%
- **Focus**: Coins with 4%+ daily move potential

## 🔧 Customization

Edit `config.py` to adjust:
- Exchanges to scan
- Minimum volume requirements
- Scan frequency
- Risk per trade

## 📞 Support

If you need help:
1. Check the console output for error messages
2. Make sure all dependencies are installed
3. Verify your Discord webhook is working



