# Quick Start - Discord Setup

Your Discord webhook is ready! Here's how to use it with the Pocket Option scanner.

## 🚀 Quick Start Commands

### Test the Webhook First

```bash
python test_discord_setup.py
```

This will send a test message to your Discord channel "POS" to verify everything works.

### Run the Scanner with Discord

**Option 1: Command Line (Recommended)**
```bash
python pocket_option_scanner.py \
  --webhook "https://discord.com/api/webhooks/1434388313141284907/QPdm7ahZUWDrtzUUZuLcWnOql71RKoscRIZu-vpbpIBJUK3iETUEXoYBEvE2uv2RXf0D" \
  --symbols "BTC/USDT,ETH/USDT,SOL/USDT" \
  --interval 60
```

**Option 2: Environment Variable**
```bash
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/1434388313141284907/QPdm7ahZUWDrtzUUZuLcWnOql71RKoscRIZu-vpbpIBJUK3iETUEXoYBEvE2uv2RXf0D"
python pocket_option_scanner.py --symbols "BTC/USDT,ETH/USDT,SOL/USDT"
```

**Option 3: Create a Startup Script**

Create `start_scanner.sh`:
```bash
#!/bin/bash
python pocket_option_scanner.py \
  --webhook "https://discord.com/api/webhooks/1434388313141284907/QPdm7ahZUWDrtzUUZuLcWnOql71RKoscRIZu-vpbpIBJUK3iETUEXoYBEvE2uv2RXf0D" \
  --symbols "BTC/USDT,ETH/USDT,SOL/USDT,EUR/USD,GBP/USD" \
  --timeframes "5m,15m" \
  --interval 60
```

Make it executable:
```bash
chmod +x start_scanner.sh
./start_scanner.sh
```

## 📊 What You'll See

When signals are detected (A+ or A grade), you'll get Discord messages like:

```
🟢 Pocket Option Signal: BTC/USDT CALL
Grade: A+ | Confidence: 85%

Entry Price: $43,250.50
Timeframe: 5m
Confluence: 85/100

Signal Type: ORB_BULLISH, SFP_SUPPORT, VOLUME, FVG_BULLISH

Reasons:
• ORB High Breakout
• Strong Support SFP (2 touches)
• High Volume (2.3x avg)
• Bullish FVG Formed
```

## ⚙️ Customization

### Change Scan Interval
```bash
# Scan every 30 seconds (faster, but more API calls)
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --interval 30

# Scan every 5 minutes (slower, less frequent)
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --interval 300
```

### Change Symbols
```bash
# Only crypto
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --symbols "BTC/USDT,ETH/USDT,SOL/USDT"

# Only forex
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --symbols "EUR/USD,GBP/USD,USD/JPY"
```

### Change Timeframes
```bash
# Only 5-minute signals
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --timeframes "5m"

# Multiple timeframes for confirmation
python pocket_option_scanner.py --webhook "YOUR_WEBHOOK" --timeframes "5m,15m,1h"
```

## 🧪 Test Mode

Run a one-time scan to test without continuous monitoring:
```bash
python pocket_option_scanner.py \
  --webhook "YOUR_WEBHOOK" \
  --oneshot
```

## 📝 Your Webhook Details

- **Channel**: POS
- **Guild ID**: 734621342069948446
- **Webhook ID**: 1434388313141284907

## ✅ Verification

1. Run `python test_discord_setup.py` - you should see a test message in your Discord
2. Run the scanner - A+ and A grade signals will be sent automatically
3. Check your Discord channel "POS" for notifications

## 🎯 Signal Grading

Only **A+ and A grade** signals are sent to Discord:
- **A+**: 85+ confluence (best signals)
- **A**: 70-84 confluence (strong signals)
- **B/C**: Logged but not sent (you can change this in code)

---

**Ready to go!** Your scanner will now send trading signals directly to your Discord channel. 🚀








