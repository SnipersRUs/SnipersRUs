# PivotX Scanner Bot

Automated scanner that detects pivot points and pullback setups across multiple timeframes.

## Features

- **Multi-Timeframe Scanning**: Scans 5m, 15m, and 1H timeframes
- **Priority Coins**: Always scans BTC, SOL, and SUI
- **Top 100 Coverage**: Scans top 100 cryptocurrencies by volume
- **Pullback Detection**: Identifies when price retraces to pivot zones
- **Watchlist Management**: Maintains 3-4 coins with best setups
- **Discord Notifications**: Sends detailed cards with pivot information
- **A+ Setup Detection**: 1H pivots are marked as highest quality

## Setup

1. **Install Dependencies**:
```bash
pip install pandas numpy requests
```

2. **Configure Discord Webhook**:
   - Update `DISCORD_WEBHOOK` in the script with your webhook URL

3. **Run the Bot**:
```bash
python3 pivotx_scanner_bot.py
```

Or run in background:
```bash
nohup python3 pivotx_scanner_bot.py > pivotx_scanner.log 2>&1 &
```

## How It Works

### Pivot Detection
- Uses ATR-based dynamic pivot strength calculation
- Detects pivot highs and lows based on surrounding bars
- Confirms pivots with ATR-based price confirmation
- Timeframe-adaptive: stricter on lower timeframes

### Setup Quality
- **A+**: 1H pivots (highest quality)
- **A**: 15m pivots
- **B**: 5m pivots

### Scoring System
- Quality bonus (A+ = 100, A = 50, B = 25)
- Confirmed pivot bonus (+30)
- Pullback bonus (+40, minus distance)
- Priority coin bonus (+20)

### Watchlist Criteria
1. Pivots with pullbacks (price retracing to zone)
2. Confirmed pivots (price closed beyond ATR threshold)
3. Highest scoring setups (top 3-4)

## Discord Cards

Each card includes:
- **Pivot Type**: HIGH (SHORT) or LOW (LONG)
- **Pivot Price**: Exact pivot level
- **Timeframe**: 5m, 15m, or 1H
- **Current Price**: Latest price
- **Distance to Pivot**: How close price is to pivot
- **Stop Placement**: Stop loss recommendation
- **Entry Zone**: Suggested entry area
- **Targets**: TP1 and TP2 levels
- **TradingView Link**: Direct chart link

## Configuration

### Scan Interval
- Default: 5 minutes
- Adjust `SCAN_INTERVAL_SEC` to change frequency

### Timeframes
- Currently: 5m, 15m, 1H
- Modify `TIMEFRAMES` list to add/remove

### Priority Coins
- Default: BTCUSDT, SOLUSDT, SUIUSDT
- Modify `PRIORITY_COINS` list

### Watchlist Size
- Default: 4 coins
- Adjust `MAX_WATCHLIST_SIZE`

### Pivot Parameters
- `ATR_MULTIPLIER`: 0.5 (higher = fewer pivots)
- `ATR_PERIOD`: 14
- `ATR_CONFIRM_MULT`: 0.2 (confirmation threshold)

## Trading Strategy

### Entry
- Enter when price pulls back to pivot zone
- Use limit orders near pivot level
- Wait for confirmation (price respecting pivot)

### Stop Loss
- **Pivot High (SHORT)**: Stop above pivot (1% above)
- **Pivot Low (LONG)**: Stop below pivot (1% below)

### Targets
- **TP1**: 2% from pivot
- **TP2**: 5% from pivot

### Best Setups
1. **1H Pivots (A+)**: Highest quality, best for swing trades
2. **15m Pivots (A)**: Good for day trading
3. **5m Pivots (B)**: Quick scalps, higher risk

## Logs

Logs are saved to `pivotx_scanner.log` with:
- Scan cycles
- Detected pivots
- Watchlist updates
- Discord notifications
- Errors and warnings

## Notes

- Bot scans every 5 minutes
- Avoids duplicate notifications
- Focuses on confirmed pivots
- Prioritizes pullback setups
- 1H pivots are marked as A+ quality

## Troubleshooting

**No pivots detected?**
- Check if symbols are trading
- Verify API connectivity
- Review log file for errors

**Too many/few signals?**
- Adjust `ATR_MULTIPLIER` (higher = fewer)
- Modify `MAX_WATCHLIST_SIZE`
- Change score threshold (currently 80)

**Discord not receiving?**
- Verify webhook URL
- Check Discord channel permissions
- Review rate limits

## Support

For issues or questions, check the logs or review the code comments.

---

**Happy Trading! 🚀**




