# Discord Post Examples

This document shows what the Traditional Markets Bot posts look like in Discord.

## 📱 Bot Startup Notification

When the bot first starts, it sends this notification:

```
🤖 Traditional Markets Bot Activated

Scan Interval: Every 4.0 hours
Schedule:
- Monday-Friday: Regular scans
- Saturday: Silent (no scans)
- Sunday: Weekly picks generated

Bot is now running and will scan markets automatically.
```

**Color:** Green

---

## 📅 Weekly Picks (Sunday)

Every Sunday, the bot generates weekly swing trade picks:

```
📅 Weekly Picks for Upcoming Week

Week Starting: January 21, 2024

### 🎯 Weekly Picks (Swing Trades)

🟢 MSFT LONG • A+
Entry: $415.80 | Stop: $408.50 | TP: $432.20
R:R 2.65:1 • Confluence: 75/100
[Chart](https://www.tradingview.com/chart/?symbol=MSFT)

🟢 NQ=F LONG • A
Entry: $17,845.00 | Stop: $17,720.00 | TP: $18,095.00
R:R 2.40:1 • Confluence: 68/100
[Chart](https://www.tradingview.com/chart/?symbol=CME_MINI:NQ1!)

🔴 GBPUSD=X SHORT • A
Entry: 1.26850 | Stop: 1.27320 | TP: 1.25800
R:R 2.30:1 • Confluence: 72/100
[Chart](https://www.tradingview.com/chart/?symbol=OANDA:GBPUSD)
```

**Color:** Blue
**Footer:** "Weekly swing trades - Daily timeframe analysis"

---

## 📊 Regular Scan (Monday-Friday)

Every 4 hours during trading days, the bot posts multiple embeds:

### 1. Stocks — Top 3 Breakout Signals

```
Stocks — Top 3 Breakout Signals

🟢 AAPL LONG • A+
Entry: $178.50 | Stop: $175.20 | TP: $184.80
R:R 2.50:1 • Confluence: 72/100
[Chart](https://www.tradingview.com/chart/?symbol=AAPL)

🔴 TSLA SHORT • A
Entry: $245.30 | Stop: $248.90 | TP: $239.20
R:R 2.30:1 • Confluence: 68/100
[Chart](https://www.tradingview.com/chart/?symbol=TSLA)

🟢 NVDA LONG • B
Entry: $128.75 | Stop: $126.50 | TP: $132.80
R:R 2.90:1 • Confluence: 58/100
[Chart](https://www.tradingview.com/chart/?symbol=NVDA)
```

**Color:** White

### 2. Futures — Daily Breakout Pick

```
Futures — Daily Breakout Pick

🟢 ES=F LONG • A
Entry: $5,845.50 | Stop: $5,820.00 | TP: $5,895.75
R:R 2.60:1 • Confluence: 65/100
[Chart](https://www.tradingview.com/chart/?symbol=CME_MINI:ES1!)
```

**Color:** Blue

### 3. Forex — Daily Breakout Pick

```
Forex — Daily Breakout Pick

🔴 EURUSD=X SHORT • A
Entry: 1.08450 | Stop: 1.08720 | TP: 1.08010
R:R 2.40:1 • Confluence: 70/100
[Chart](https://www.tradingview.com/chart/?symbol=OANDA:EURUSD)
```

**Color:** Orange

### 4. Paper Trading Status

```
Paper Trading Status

Balance: $10,245.50
Open Positions: 2
Wins/Losses: 8/3
Realized PnL: $+245.50
Unrealized PnL: $+89.20
```

**Color:** Green

---

## 🎉 Position Closed (Take Profit)

When a position hits take profit:

```
🎉 Position Closed: AAPL LONG

Reason: TAKE PROFIT
Entry: $178.50
Exit: $184.80
PnL: $+157.50 (+2.5%)
Balance: $10,157.50
```

**Color:** Green
**Footer:** "AAPL 1h • A+ signal"

---

## 🛑 Position Closed (Stop Loss)

When a position hits stop loss:

```
🛑 Position Closed: TSLA SHORT

Reason: STOP LOSS
Entry: $245.30
Exit: $248.90
PnL: $-108.00 (-1.5%)
Balance: $9,892.00
```

**Color:** Red
**Footer:** "TSLA 1h • A signal"

---

## 📋 Signal Grades

- **A+**: All 3 indicators aligned (GPS + Head Hunter + Oath Keeper)
- **A**: 2 indicators + high confluence (≥70)
- **B**: 2 indicators aligned
- **C**: Basic signal (usually filtered out)

## 🔗 TradingView Links

All signals include direct TradingView chart links:
- Stocks: Direct symbol (e.g., `AAPL`)
- Futures: CME format (e.g., `CME_MINI:ES1!`)
- Forex: OANDA format (e.g., `OANDA:EURUSD`)

## 📅 Schedule

- **Monday-Friday**: Regular 4-hour scans (6 scans per day)
- **Saturday**: Silent mode (no posts)
- **Sunday**: Weekly picks + regular scans

---

## Testing

To see these examples in your Discord:

```bash
# Install dependencies if needed
pip install requests python-dotenv

# Set WEBHOOK in .env file first!
# Then run:
python test_discord_examples.py all
```

Or test individual examples:
```bash
python test_discord_examples.py startup  # Bot startup
python test_discord_examples.py weekly  # Weekly picks
python test_discord_examples.py scan    # Regular scan
python test_discord_examples.py tp      # Take profit
python test_discord_examples.py sl      # Stop loss
```
