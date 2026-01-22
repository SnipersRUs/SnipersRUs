# Sniper Guru Bot

Enhanced BTC NY session analysis bot with Discord webhook integration, sentiment analysis, and advanced technical indicators.

## Features

- **Discord Webhook Integration**: Sends pings when active and full analysis reports
- **Advanced Technical Analysis**:
  - Moving averages (20, 50, 200)
  - VWAP calculations (1H, 4H, Weekly, Monthly, Yearly)
  - ATR and MFI indicators
  - Liquidity flush detection
  - Trend scoring system
- **Sentiment Analysis**: News and social media sentiment scoring
- **Macro Data**: SPY, VIX, DXY, WTI, Gold prices
- **Fed Calendar**: Upcoming Fed meetings and minutes
- **Memory System**: Performance tracking and learning from past trades

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Commands

```bash
# Send ping to Discord (shows bot is active)
python3 sniper_guru_bot.py --ping

# Run analysis now (console output only)
python3 sniper_guru_bot.py --now

# Run analysis and post to Discord
python3 sniper_guru_bot.py --now --post

# Run in scheduled loop mode (daily at 8:55 AM NY time)
python3 sniper_guru_bot.py --loop

# Run in loop mode with Discord posting
python3 sniper_guru_bot.py --loop --post
```

### Using the Run Script

```bash
# Send ping
python3 run_sniper_guru.py --ping

# Run analysis now
python3 run_sniper_guru.py --now

# Run analysis and post to Discord
python3 run_sniper_guru.py --now --post

# Run in loop mode
python3 run_sniper_guru.py --loop --post
```

## Configuration

The bot uses the following Discord webhook:
```

```

## Key Features

### Ping System
- Sends a ping to Discord when the bot is active
- Rate limited to once every 5 minutes
- Shows bot status and next update time

### Analysis Report
- **Quick Market Read**: Current price, ATR, MFI
- **Indicator Analysis**: Trend score, moving averages, VWAP levels
- **Liquidity Hunter**: Detects recent volume flushes
- **Bias & Probabilities**: Up/Down/Range probabilities with components
- **Macro Events**: Fed calendar and upcoming meetings
- **Macro Snapshot**: SPY, VIX, DXY, WTI, Gold data
- **News Sentiment**: RSS feed sentiment analysis
- **X/Twitter Sentiment**: Social media sentiment
- **Performance Memory**: Trade history and win rate
- **NY Open Playbook**: Trading strategies and rules

### Scheduled Execution
- Runs daily at 8:55 AM New York time
- Can be run manually with `--now` flag
- Loop mode for continuous operation

## Technical Indicators

- **Trend Score**: 0-10 scale based on MA alignment and price action
- **VWAP Stack**: Multiple timeframe VWAP analysis
- **Liquidity Flushes**: Volume surge detection (>2.5x average)
- **Money Flow Index**: 14-period MFI for momentum
- **ATR**: 14-period Average True Range for volatility

## Memory System

The bot tracks performance in `sniperguru_memory.csv`:
- Date, setup type, signal, entry/exit prices
- PnL and win/loss tracking
- Win rate calculation for probability adjustments

## Logging

All activity is logged to `sniper_guru_bot.log` with timestamps and detailed information.

## Dependencies

- requests: HTTP requests for APIs and webhooks
- pandas: Data manipulation and analysis
- numpy: Numerical computations
- pytz: Timezone handling
- feedparser: RSS feed parsing
- schedule: Task scheduling
- beautifulsoup4: HTML parsing for Fed calendar



