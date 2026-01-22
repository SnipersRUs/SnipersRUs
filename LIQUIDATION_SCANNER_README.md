# Liquidation Scanner Bot

A professional bot that scans cryptocurrency markets for coins approaching liquidation levels on multiple timeframes.

## Features

- **Multi-Timeframe Scanning**: Monitors 15-minute, 1-hour, and daily timeframes
- **Multi-Exchange Support**: Scans MEXC, Bybit, and Binance
- **Liquidation Detection**: Uses advanced Pine Script logic to detect major liquidation events
- **Distance Tracking**: Alerts when price is within 3% of liquidation levels
- **Colored Discord Cards**:
  - **15-minute**: White cards (0xFFFFFF)
  - **1-hour**: Green cards (0x00FF00)
  - **Daily**: Red cards (0xFF0000)

## How It Works

The bot implements the Liquidation Reversal Hunter indicator logic from Pine Script:

1. **Volume Analysis**: Detects abnormal volume spikes using Z-score calculations
2. **Liquidation Size**: Calculates liquidation size based on volume and price range
3. **Importance Scoring**: Assigns importance scores (0-100) based on:
   - Volume abnormality (0-40 points)
   - Liquidation size (0-30 points)
   - Price range vs ATR (0-20 points)
   - Wick rejection (0-10 points)
4. **Level Detection**: Identifies liquidation levels:
   - **TOP (Long liquidation)**: When longs get liquidated at highs
   - **BOTTOM (Short liquidation)**: When shorts get liquidated at lows
5. **Distance Monitoring**: Tracks how close current price is to liquidation levels

## Configuration

### Discord Webhook
The bot sends alerts to:
```

```

### Liquidation Parameters
```python
LIQUIDATION_PARAMS = {
    'volume_multiplier': 2.5,
    'volume_lookback': 50,
    'min_liquidation_size': 5.0,
    'z_score_threshold': 2.0,
    'min_importance_for_signal': 40.0,
    'max_distance_pct': 3.0  # Alert if within 3% of liquidation level
}
```

### Timeframes
- **15m**: 100 bars lookback, White cards
- **1h**: 200 bars lookback, Green cards
- **1d**: 200 bars lookback, Red cards

## Usage

### Run Once
```bash
python run_liquidation_scanner.py
```

### Run Continuously
```bash
python liquidation_scanner_bot.py
```

The bot will:
1. Scan all configured exchanges
2. Check each symbol on all timeframes
3. Detect liquidation levels
4. Calculate distance to current price
5. Send Discord alerts for coins within 3% of liquidation levels
6. Repeat every 45 minutes

## Discord Message Format

Each timeframe gets its own embed with:
- Symbol name (clickable TradingView link)
- Exchange name
- Liquidation type (TOP/BOTTOM)
- Importance score
- Liquidation level price
- Current price
- Distance percentage
- Liquidation size

## Example Output

```
⏰ 15-Minute Liquidation Scanner
Found 5 coins approaching liquidations

1. BTC/USDT:USDT (MEXC)
🔴 TOP (Longs) | 🔥 Importance: 75%
Level: $45,200.00 | Current: $44,850.00
🎯 Distance: 0.78%
Size: 12.50M
```

## Requirements

- Python 3.8+
- ccxt
- pandas
- numpy
- requests

Install dependencies:
```bash
pip install ccxt pandas numpy requests
```

## Risk Warning

⚠️ **Educational tool only. Not financial advice.**

These liquidation levels are potential zones where price may react. Always use proper risk management:
- Use stop losses
- Don't risk more than 1-2% per trade
- These are potential reversal zones, not guaranteed signals
- Market conditions can change rapidly

## Technical Details

### Liquidation Detection Logic

1. **Volume Z-Score**: `(volume - avg_volume) / volume_std`
2. **Liquidation Size**: `(volume / 1e6) * price_range`
3. **Major Liquidation**: Triggered when:
   - Liquidation size >= 5M, OR
   - Abnormal volume (Z >= 2.0) AND liquidation Z >= 1.6, OR
   - Very abnormal volume (Z >= 3.0)

### Importance Calculation

- **Volume Component** (0-40 pts):
  - Very abnormal (Z >= 3.0): 40 pts
  - Abnormal (Z >= 2.0): 25 pts
  - Above multiplier: 10 pts

- **Liquidation Size** (0-30 pts):
  - Z >= 3.0: 30 pts
  - Z >= 2.0: 20 pts
  - Size >= 5M: 10 pts

- **Price Range** (0-20 pts):
  - Range/ATR > 3.0: 20 pts
  - Range/ATR > 2.0: 15 pts
  - Range/ATR > 1.5: 10 pts

- **Wick Rejection** (0-10 pts):
  - Wick ratio > 0.6: 10 pts
  - Wick ratio > 0.4: 5 pts

## Troubleshooting

### No signals found
- Check if markets are active
- Verify exchange connections
- Adjust `max_distance_pct` if needed
- Lower `min_importance_for_signal` for more signals

### Discord errors
- Verify webhook URL is correct
- Check internet connection
- Ensure webhook has proper permissions

### Exchange errors
- Check API rate limits
- Verify exchange credentials (if needed)
- Some exchanges may require API keys for futures data

## License

Educational use only. Not for commercial distribution.
