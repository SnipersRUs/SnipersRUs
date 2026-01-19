# Piv X Signal Bot for Discord

A Discord signal bot that implements the **Piv X indicator** logic for BTC, SOL, and ETH with hourly scanning and intelligent trade state tracking.

## Features

- **Hourly Scanning**: Scans BTC, SOL, and ETH every hour
- **Smart Trade Tracking**: No duplicate signals - if same trade is still valid, marks as "Still Valid"
- **Entry Waiting**: Bot detects setups but waits for price to reach entry zone before triggering "OPEN" alert
- **Full Trade Lifecycle**: SETUP → ENTRY → OPEN → TARGET1 → TARGET2 → STOP alerts
- **Risk Model**: Targets 2% moves with max 3% stop, 15x leverage displayed
- **Grouped Cards**: Same direction trades grouped on same Discord card
- **Color Coded**: White cards for bullish (LONG), Purple cards for bearish (SHORT)
- **Confluence Scoring**: Based on Piv X + Williams Divergence (RSI, volume, exhaustion, MA trend, HTF alignment, WillR divergence)

## Discord Card Types

| Alert Type | Description |
|------------|-------------|
| 📊 SETUP | New pivot zone detected, waiting for entry |
| 🎯 ENTRY | Price approaching entry zone |
| ✅ OPEN | Entry triggered, trade is live |
| 🎯 TARGET1 | First profit target (2%) |
| 🏁 TARGET2 | Second profit target (4%) |
| 🛑 STOP | Stop loss hit |
| ♻️ STILL_VALID | Existing setup still active on rescan |

## Card Colors

- **White (0xFFFFFF)**: Bullish / LONG setups
- **Purple (0x9B59B6)**: Bearish / SHORT setups
- **Blue (0x3498DB)**: Hourly update / status cards

## How It Works

1. **Pivot Detection**: Scans for pivot highs and lows using dynamic strength based on ATR
2. **Confluence Scoring**: Calculates a 0-100 score based on:
   - Volume spike (+15)
   - HTF trend alignment (+20)
   - RSI oversold/overbought (+25)
   - Exhaustion signals (+10)
   - ATR confirmation (+10)
   - MA trend alignment (+15)
3. **Signal Generation**: Only signals with score ≥60 are generated, one per coin per scan
4. **Trade Tracking**: Stores trades in SQLite database to avoid duplicates
5. **Entry Monitoring**: Monitors price until entry zone is reached
6. **Exit Monitoring**: Tracks stop loss and target levels
7. **Entry Distance**: Alerts include % distance to entry for planning

## Configuration

Edit the constants at the top of `pivx_signal_bot.py`:

```python
SCAN_INTERVAL_SEC = 60 * 60  # 1 hour (change for faster scanning)
SYMBOLS = ["BTCUSDT", "SOLUSDT", "ETHUSDT"]  # Add more symbols
TIMEFRAMES = ["15m", "1h", "4h"]  # Timeframes for analysis
PRIMARY_TIMEFRAME = "1h"  # Main signal timeframe
WILLR_LENGTH = 14
WILLR_OB_LEVEL = -20
WILLR_OS_LEVEL = -80
MIN_CONFLUENCE_SCORE = 60
LEVERAGE = 15
TARGET_PCT = 0.02
SECOND_TARGET_PCT = 0.04
STOP_PCT = 0.03
```

## Quick Start

### Option 1: Run Script
```bash
chmod +x run_pivx_signal_bot.sh
./run_pivx_signal_bot.sh
```

### Option 2: Direct Python
```bash
# Install dependencies
pip install ccxt pandas numpy requests

# Run the bot
python3 pivx_signal_bot.py
```

### Option 3: Background Process
```bash
nohup python3 pivx_signal_bot.py > pivx_bot.log 2>&1 &
echo $! > pivx_bot.pid
```

To stop:
```bash
kill $(cat pivx_bot.pid)
```

## Database

The bot uses SQLite to track trades. Database file: `pivx_trades.db`

### Tables

- **trades**: Stores all trade signals and their states
- **alerts_sent**: Tracks which alerts have been sent (prevents duplicates)

### View Active Trades
```bash
sqlite3 pivx_trades.db "SELECT symbol, direction, status, entry_price FROM trades WHERE status IN ('pending', 'open', 'valid');"
```

## Logs

Logs are written to `pivx_signal_bot.log` and stdout.

## Discord Webhook

The webhook is configured in the bot:
```python
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1461253818082918534/..."
```

## Example Discord Cards

### New Setup (Bullish)
```
┌─────────────────────────────────────┐
│ Piv X Signal - BTC                  │
├─────────────────────────────────────┤
│ 🟢 LONG | 📊 SETUP                  │
│                                     │
│ Pivot LOW: $94,500.00               │
│ Entry Zone: $94,600.00              │
│ Stop Loss: $94,000.00               │
│ Target 1: $95,800.00                │
│ Target 2: $97,000.00                │
│                                     │
│ Current Price: $94,750.00           │
│ Confluence Score: 75/100            │
│ RSI: 28.5                           │
│ Volume Spike: ✅                    │
│ Exhaustion: ✅                      │
│                                     │
│ Timeframe: 1h                       │
└─────────────────────────────────────┘
```

### Hourly Update
```
┌─────────────────────────────────────┐
│ ♻️ Piv X - Hourly Scan Update       │
├─────────────────────────────────────┤
│ Active Setups Still Valid:          │
│                                     │
│ 🟢 LONGS:                           │
│ • BTC: Entry $94,600 | Score 75     │
│ • SOL: Entry $185.50 | Score 68     │
│                                     │
│ 🟣 SHORTS:                          │
│ • ETH: Entry $3,450 | Score 72      │
│                                     │
│ Last scan: 14:00 UTC                │
└─────────────────────────────────────┘
```

## Piv X Indicator Logic

The bot implements key logic from the Piv X TradingView indicator:

1. **Dynamic Pivot Detection**: ATR-based pivot strength
2. **Volume Confirmation**: Requires volume spike > 1.5x average
3. **RSI Zones**: Oversold (<35) for longs, Overbought (>65) for shorts
4. **MA Trend Filter**: 12/26 EMA crossover
5. **HTF Trend Alignment**: 4H EMA for trend direction
6. **Exhaustion Detection**: Price move + volume spike pattern

## Customization

### Add More Symbols
```python
SYMBOLS = ["BTCUSDT", "SOLUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT"]
```

### Change Scan Interval
```python
SCAN_INTERVAL_SEC = 30 * 60  # 30 minutes
```

### Adjust Confluence Threshold
In `scan_symbol()` method:
```python
if score >= 60:  # Higher = fewer signals
```

## Troubleshooting

### No Signals Generated
- Check if market has clear pivot patterns
- Lower the confluence score threshold (default 50)
- Check logs for errors

### Exchange Rate Limits
- The bot includes delays between API calls
- If still hitting limits, increase `time.sleep()` values

### Database Locked
- Only run one instance of the bot at a time
- Delete `pivx_trades.db` to start fresh

## Support

This bot is part of the SnipersRUs trading toolkit. For issues or feature requests, check the repository.
