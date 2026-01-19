# Traditional Markets Breakout Bot

Applies the GPS + Head Hunter + Oath Keeper trading logic from `breakout_prop_bot.py` to traditional markets (stocks, futures, forex).

## Features

- **4-Hour Scan Schedule**: Automatically scans markets every 4 hours
- **Saturday Silent Mode**: Bot goes silent on Saturdays (no scans/notifications)
- **Weekly Picks**: Generates weekly swing trade picks every Sunday for the upcoming week
- **Multiple Free API Providers**: Uses yfinance (primary), with fallbacks to Alpha Vantage, Polygon.io, Finnhub, and Stooq
- **Real-time Data**: Fetches live prices with automatic fallback chains
- **Breakout Trading Logic**:
  - **GPS (Golden Pocket Syndicate)**: Golden pocket retracements, order blocks, liquidity sweeps, Wave Trend
  - **Head Hunter**: VWAP-based signals with band taps
  - **Oath Keeper**: Money flow divergences and major pivot detection
- **Paper Trading**: Automatic position management with TP/SL monitoring
- **Discord Notifications**: Real-time alerts for signals and closed positions

## Setup

### 1. Environment Variables

Create/update `.env` file:

```bash
WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK
SCAN_INTERVAL=14400           # Scan every 4 hours (14400 seconds = 4 hours)
ACCOUNT_SIZE=10000            # Starting paper trading balance
RISK_PER_TRADE=0.015         # 1.5% risk per trade

# Optional API keys (improves data reliability):
ALPHA_VANTAGE_API=your_key    # Free tier: 500 calls/day
POLYGON_API=your_key          # Free tier: 5 calls/min
FINNHUB_API=your_key          # Free tier: 60 calls/min
```

### 2. Get Free API Keys (Optional but Recommended)

**Alpha Vantage** (500 calls/day free):
- Sign up at: https://www.alphavantage.co/support/#api-key
- Good for stocks historical data

**Polygon.io** (5 calls/min free):
- Sign up at: https://polygon.io/
- Excellent for stocks and options

**Finnhub** (60 calls/min free):
- Sign up at: https://finnhub.io/
- Great for real-time stock data

**Note**: The bot works without API keys using yfinance and Stooq, but API keys improve reliability and reduce rate limiting.

### 3. Install Dependencies

```bash
pip install pandas numpy yfinance requests feedparser python-dotenv certifi
```

### 4. Run

**One-time scan:**
```bash
python traditional_markets_bot.py once
```

**Generate weekly picks (Sunday):**
```bash
python traditional_markets_bot.py weekly
```

**Continuous scanning (default - runs every 4 hours, silent on Saturday):**
```bash
python traditional_markets_bot.py
```

## Schedule

The bot runs on a weekly schedule:

- **Monday-Friday**: Regular scans every 4 hours (default: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
- **Saturday**: Silent mode - no scans or notifications
- **Sunday**: Generates weekly picks for the upcoming week + regular 4-hour scans

### Weekly Picks

Every Sunday, the bot:
1. Scans all markets using **daily timeframe** (swing trades)
2. Selects best weekly picks for stocks, futures, and forex
3. Posts a dedicated "Weekly Picks" embed with entry/stop/target levels
4. Saves picks to state file for reference throughout the week

## How It Works

### Signal Generation

The bot requires **2 out of 3 confirmations** from:
1. **GPS Signal**: Confluence score ≥55 with golden pocket proximity, order blocks, or sweeps
2. **Head Hunter Signal**: VWAP band taps with volume confirmation
3. **Oath Keeper Signal**: Major divergences or extreme money flow readings

### Signal Grades

- **A+**: All 3 indicators aligned
- **A**: 2 indicators + confluence ≥70
- **B**: 2 indicators aligned
- **C**: Basic signal (usually filtered out)

### Position Management

- **Risk**: 1.5% of account per trade (configurable)
- **Stop Loss**: Based on ATR and recent swing levels
- **Take Profit**: 2.5R minimum (risk:reward ratio)
- **Max Position Size**: 30% of account per trade

### Markets Scanned

**Stocks** (default):
- AAPL, MSFT, NVDA, AMZN, META, AMD, TSLA, GOOGL, PLTR, IONQ, RKLB

**Futures** (default):
- ES=F (S&P 500), NQ=F (Nasdaq), YM=F (Dow), CL=F (Crude), GC=F (Gold)

**Forex** (default):
- EURUSD=X, GBPUSD=X, USDJPY=X, AUDUSD=X, USDCAD=X

Modify lists in `traditional_markets_bot.py` to customize.

## Paper Trading

The bot automatically:
- Opens paper trades on A+ or A grade signals
- Monitors positions for TP/SL hits
- Updates unrealized PnL
- Closes positions and updates balance
- Tracks win/loss statistics

State is saved in `traditional_markets_state.json`.

## Discord Output

The bot posts embeds for:
- **Stocks**: Top 3 breakout signals
- **Futures**: Best daily pick
- **Forex**: Best daily pick
- **Paper Trading Status**: Balance, open positions, PnL

## API Fallback Chain

For each symbol, the bot tries:
1. **yfinance** (primary, free)
2. **Alpha Vantage** (if API key provided)
3. **Polygon.io** (if API key provided)
4. **Finnhub** (if API key provided)
5. **ETF Proxy** (for futures: SPY for ES=F, QQQ for NQ=F, etc.)
6. **Stooq** (final fallback, no API key)

## Rate Limiting

The bot automatically manages rate limits:
- **Alpha Vantage**: 1 call per 60 seconds
- **Polygon**: 5 calls per 60 seconds
- **Finnhub**: 60 calls per 60 seconds

Built-in delays prevent hitting free tier limits.

## Troubleshooting

**No signals detected:**
- Check if symbols are valid
- Verify data is fetching (check logs)
- Adjust signal thresholds if needed

**Rate limit errors:**
- Add API keys for better reliability
- Increase `SCAN_INTERVAL` to reduce call frequency

**SSL/Certificate errors:**
- Bot uses `certifi` bundle automatically
- Should work on macOS without issues

## Example Output

**Regular Scan (Monday-Friday):**
```
🔍 Starting market scan...
[INFO] Paper trade opened: TM_1234567890_AAPL
✅ Posted 4 embeds to Discord
✅ Scan complete
💤 Sleeping 14400s (4.0 hours)...
```

**Saturday:**
```
🔇 Saturday - Silent mode, skipping scan
💤 Sleeping 14400s...
```

**Sunday (Weekly Picks):**
```
📅 Sunday detected - Generating weekly picks...
📅 Running weekly analysis for upcoming week...
✅ Posted weekly picks to Discord
🔍 Starting market scan...
✅ Posted 5 embeds to Discord
✅ Scan complete
```

## Customization

Edit in `traditional_markets_bot.py`:
- `STOCKS`, `FUTURES`, `FOREX` lists (line ~47)
- Signal thresholds in `gps_signal()`, `head_hunter_signal()`, `oath_keeper_signal()`
- Risk parameters in `.env`

## Notes

- **Real-time**: Uses latest candles + yfinance info for current price
- **Delayed data**: Free tiers may have 15-min delays for some exchanges
- **Paper trading only**: No live execution (safety first!)
- **Best for**: Swing/day trading signals, not scalping

## Credits

- GPS/Head Hunter/Oath Keeper logic adapted from `breakout_prop_bot.py`
- Market Pulse structure inspired by `market_pulse.py`
- Free API integrations for traditional markets
