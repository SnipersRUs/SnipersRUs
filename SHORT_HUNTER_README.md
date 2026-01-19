# Short Hunter Bot 🎯

A specialized bot that finds the best **SHORT opportunities** at tops and resistances for reversal trades.

## Features

- **SHORT-Only Focus**: Scans exclusively for reversal opportunities at tops/resistances
- **Deviation VWAP Analysis**: Uses 2σ (A+) and 3σ (A++) deviation levels for high-quality setups
- **Wave 5 Detection**: Identifies completed Elliott Wave 5 patterns as main catalyst
- **SFP Detection**: Detects Fair Value Gaps (SFPs) for additional confirmation
- **Resistance Analysis**: Finds key resistance levels and calculates percentage from top
- **15m+ Timeframes**: Scans 15m, 1h, and 4h timeframes for optimal entries
- **Discord Notifications**: Posts to Discord with @here pings using your webhook

## Requirements

- Python 3.7+
- Required packages: `ccxt`, `pandas`, `numpy`, `requests`

## Configuration

The bot uses the Discord webhook configured in the code:
```
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1444925694290300938/..."
```

## Usage

### Single Scan
```bash
python3 short_hunter_bot.py
```

### Continuous Mode (scans every 45 minutes)
```bash
python3 short_hunter_bot.py continuous
```

Or use the run script:
```bash
./run_short_hunter.sh
```

## Output

Each scan returns:
- **Top 2 SHORT Signals**: Best reversal setups with:
  - Deviation VWAP level (2σ = A+, 3σ = A++)
  - Wave 5 completion or SFP detection
  - Percentage from top
  - Resistance proximity
  - RSI and volume analysis
  - TradingView chart links

- **Watchlist (3 coins)**: Coins approaching resistances within 5% of their tops

## Signal Criteria

A SHORT signal requires:
1. **Minimum 2σ deviation** above VWAP (A+ setup)
2. **3σ deviation** = A++ setup (highest quality)
3. **Main Catalyst**: Either:
   - Finished Wave 5 pattern, OR
   - Bearish SFP (Fair Value Gap) detection
4. **Additional Factors**:
   - Near resistance levels
   - High volume confirmation
   - RSI overbought (>60)
   - Percentage from top calculation

## Scoring System

Signals are scored based on:
- **Deviation Level**: 3σ (30 pts), 2σ (20 pts)
- **Wave 5 Complete**: 25 pts
- **SFP Detection**: 20 pts
- **Near Resistance**: 15 pts
- **Volume Spike**: 10 pts (1.5x+), 5 pts (1.2x+)
- **RSI Overbought**: 10 pts (>70), 5 pts (>60)

Top 2 signals are selected based on highest scores.

## Discord Notifications

The bot posts embeds to Discord with:
- @here ping for immediate attention
- Detailed signal cards with all analysis
- TradingView chart links
- Watchlist of approaching resistances

## Exchanges Supported

- Bybit
- Bitget
- MEXC

Scans ~500 USDT perpetual markets across these exchanges.

## Timeframes

- **15m**: Primary entry timeframe
- **1h**: Confirmation timeframe
- **4h**: Higher timeframe context

## Notes

- The bot only looks for SHORT opportunities (reversal at tops)
- Requires strong catalyst (Wave 5 or SFP) for signal generation
- Focuses on coins near resistances or within 5% of recent tops
- Scans every 45 minutes in continuous mode
