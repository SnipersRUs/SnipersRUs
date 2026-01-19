# Pocket Option Market Scanner Bot

A Python bot that scans underlying markets to generate accurate trading signals for binary options on Pocket Option.

## 🎯 How It Works

Pocket Option doesn't have a public API, but their prices are derived from real underlying markets. This bot:
1. **Fetches real market data** from exchanges (Binance, Bybit, etc.)
2. **Applies your Bounty Seeker logic** (ORB, FVG, SFP, Single Prints, Pivots)
3. **Generates binary options signals** (CALL/PUT) with confidence scores
4. **Sends notifications** via Discord webhook

## 📊 Signal Detection Methods

The bot uses the same logic from your `bounty_seeker_orb_enhanced_improved.pine` script:

- **ORB (Opening Range Breakout)**: Detects breakouts from first 15 minutes
- **FVG (Fair Value Gaps)**: Identifies price gaps with volume confirmation
- **SFP (Support/Resistance Points)**: Tracks pivot levels with touch counting
- **Single Prints**: Finds unique price levels that may act as support/resistance
- **Volume Analysis**: Confirms signals with volume spikes

## 🚀 Usage

### Basic Setup

```bash
# Install dependencies (if not already installed)
pip install ccxt pandas numpy requests

# Run continuous scanning (default: BTC, ETH, SOL, EUR/USD, GBP/USD)
python pocket_option_scanner.py
```

### Command Line Options

```bash
# Scan specific symbols
python pocket_option_scanner.py --symbols "BTC/USDT,ETH/USDT,SOL/USDT"

# Set scan interval (seconds)
python pocket_option_scanner.py --interval 30

# Multiple timeframes
python pocket_option_scanner.py --timeframes "5m,15m,1h"

# Discord notifications
python pocket_option_scanner.py --webhook "YOUR_DISCORD_WEBHOOK_URL"

# One-time scan (for testing)
python pocket_option_scanner.py --oneshot
```

### Environment Variables

```bash
export SYMBOLS="BTC/USDT,ETH/USDT,SOL/USDT"
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjkl..."
export TELEGRAM_CHAT_ID="123456789"
export SCAN_INTERVAL=60

python pocket_option_scanner.py
```

## 📈 Signal Grading

Signals are graded based on confluence score:

- **A+**: 85+ confluence (multiple confirmations)
- **A**: 70-84 confluence (strong signals)
- **B**: 60-69 confluence (good signals)
- **C**: 50-59 confluence (basic signals)

Only signals with 50+ confluence are generated.

## 🔔 Notifications

The bot supports **both Discord and Telegram** notifications!

### Discord Notifications

```bash
# Set Discord webhook
python pocket_option_scanner.py --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Telegram Notifications

**Quick Setup:**
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your chat ID (see [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md))
3. Configure the bot:

```bash
# Method 1: Command line
python pocket_option_scanner.py \
  --telegram-token "YOUR_BOT_TOKEN" \
  --telegram-chat-id "YOUR_CHAT_ID"

# Method 2: Environment variables
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
python pocket_option_scanner.py

# Method 3: Use both Discord + Telegram
python pocket_option_scanner.py \
  --webhook "YOUR_DISCORD_WEBHOOK" \
  --telegram-token "YOUR_BOT_TOKEN" \
  --telegram-chat-id "YOUR_CHAT_ID"
```

**📱 For detailed Telegram setup instructions, see [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)**

### Notification Details

Both Discord and Telegram send notifications for:
- All **A+ and A grade** signals
- Signal details including:
  - Direction (CALL/PUT)
  - Entry price
  - Confidence score
  - Confluence breakdown
  - Signal types (ORB, FVG, SFP, etc.)

## ⚙️ Configuration

Edit the scanner initialization to customize:

```python
scanner = PocketOptionScanner(
    webhook_url="YOUR_WEBHOOK",
    symbols=['BTC/USDT', 'ETH/USDT', 'EUR/USD']  # Your symbols
)

# Adjust detection parameters
scanner.pivot_lookback = 10  # Bars to look back for pivots
scanner.min_volume_mult = 1.0  # Minimum volume multiplier
scanner.strong_volume_mult = 1.5  # Strong volume threshold
scanner.min_touches_for_strong = 2  # Touches needed for strong SFP
```

## 🎯 Trading Strategy

1. **Wait for high-grade signals** (A+ or A)
2. **Check confluence** - more confirmations = better
3. **Verify on multiple timeframes** - use `--timeframes "5m,15m"` for confirmation
4. **Enter binary options trade** on Pocket Option based on signal direction:
   - `CALL` signal → Buy CALL option
   - `PUT` signal → Buy PUT option

## ⚠️ Important Notes

1. **Test First**: Always test on demo account before live trading
2. **Risk Management**: No bot guarantees profits - use proper risk management
3. **Market Conditions**: Signals work best in trending markets
4. **Latency**: Real market data has slight latency vs Pocket Option's prices
5. **Regulations**: Ensure automated trading is legal in your jurisdiction

## 🔧 Troubleshooting

**No signals found?**
- Market may be ranging (signals work best in trends)
- Try different timeframes
- Check if symbols are available on exchange

**Connection errors?**
- Bot will automatically try backup exchanges
- Check internet connection
- Verify symbol format matches exchange

**Discord notifications not working?**
- Verify webhook URL is correct
- Check that webhook has permission to post
- Only A+ and A signals trigger notifications by default

**Telegram notifications not working?**
- See [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md) for detailed setup
- Make sure you sent at least one message to your bot first
- Verify bot token and chat ID are correct
- Check that bot is added to group (if using group chat)

## 📝 Example Output

```
🔍 Scanning 5 symbols...
✅ BTC/USDT: 1 signal(s) found
   PUT A - 78% - ORB_BEARISH, SFP_RESISTANCE, VOLUME
✅ ETH/USDT: 1 signal(s) found
   CALL B - 65% - FVG_BULLISH, SFP_SUPPORT

✅ Found 2 signal(s):
   BTC/USDT PUT (A) - 78% confidence
   ETH/USDT CALL (B) - 65% confidence
```

## 🔄 Integration with Trading

You can extend this bot to:
1. **Auto-trade**: Add Pocket Option API integration (unofficial APIs available)
2. **Filter by timeframe**: Only trade 5m signals, ignore others
3. **Backtesting**: Save signals to CSV for analysis
4. **Alerts**: Telegram notifications are already supported! ✅

---

**Remember**: This bot provides signals based on technical analysis. Always do your own research and never risk more than you can afford to lose.
