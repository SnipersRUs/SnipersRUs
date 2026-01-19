# Forex Pivot Reversal Bot

A specialized forex trading bot that focuses on **pivots and reversals** using three powerful indicators:

1. **PivotX Pro** - Dynamic pivot detection with ATR-based strength
2. **Golden Pocket Syndicate (GPS)** - Golden pocket zone identification (0.618/0.65)
3. **Tactical Deviation** - VWAP deviation bands (±1σ, ±2σ, ±3σ)

## 🎯 Key Features

### Signal Grading System
- **A+ Setups**: 15-minute and higher timeframes with strong confluence
  - Near Golden Pocket zones
  - ±3σ deviation (extreme moves)
  - Pivot reversals with exhaustion signals
- **A- Setups**: 5-minute timeframes or ±2σ deviations
  - Good for scalping opportunities
  - Lower confluence but still valid setups

### Paper Trading Configuration
- **Starting Balance**: $1,000
- **Leverage**: 150x
- **Trade Size**: $50 per trade (notional = $7,500 with 150x leverage)
- **Max Open Positions**: 3 trades simultaneously
- **Take Profit Management**:
  - 25% of position closes at TP1
  - Remaining 75% targets TP2 and TP3

### Discord Alerts

The bot sends three types of alert cards:

1. **Golden Pocket Proximity Alerts** 🎯
   - Shows distance to approaching golden pocket zones
   - Alerts when price is within 1% of GP zone
   - Rate limited: once per hour per symbol

2. **A- Deviation Setup Cards** 📊
   - Purple cards for bearish (SHORT) setups
   - Green cards for bullish (LONG) setups
   - Shows ±2σ deviation levels
   - Includes VWAP and current price

3. **A+ Setup Cards** ⭐
   - Purple cards for bearish (SHORT) setups
   - Green cards for bullish (LONG) setups
   - Includes entry, stop loss, and all TP levels
   - Shows confluence factors and reasons

## 📊 Indicator Logic

### PivotX Pro
- **Dynamic Pivot Strength**: Based on ATR and timeframe
  - 15+ pivot strength = stronger signals
  - Higher timeframes = stronger pivots
  - 5m: Minimum 5 bars, max 15 bars
  - 15m+: Minimum 2 bars, max 20-50 bars
- **Exhaustion Detection**: Identifies selling/buying exhaustion
- **Volume Spike Confirmation**: Requires 1.5x average volume

### Golden Pocket Syndicate
- Calculates daily GP zones (0.618 and 0.65 Fibonacci levels)
- Tracks proximity to GP zones
- Alerts when price approaches or touches GP

### Tactical Deviation
- **Daily VWAP** with standard deviation bands
- **Deviation Levels**:
  - ±1σ: Normal deviation
  - ±2σ: A- setup (good reversal opportunity)
  - ±3σ: A+ setup (extreme reversal opportunity)
- **Volume Confirmation**: Signals require volume spikes

## 🚀 Usage

### Basic Setup

1. **Install Dependencies**:
```bash
pip install pandas numpy ccxt requests
```

2. **Configure Discord Webhook** (already set in code):
```python
DISCORD_WEBHOOK = "your_webhook_url"
```

3. **Run the Bot**:
```bash
python run_forex_bot.py
```

### Forex Pairs

The bot scans these 3 pairs:
- **USD/JPY** - US Dollar / Japanese Yen
- **EUR/USD** - Euro / US Dollar
- **GBP/USD** - British Pound / US Dollar

You can modify `FOREX_PAIRS` in the bot file to add/remove pairs.

## 📈 Trading Rules

### Entry Criteria (A+ Setups)
1. **Pivot Detection**: Strong pivot on 15m+ timeframe
2. **Golden Pocket**: Price near or at GP zone
3. **Deviation**: ±2σ or ±3σ from VWAP
4. **Exhaustion**: Selling/buying exhaustion signal
5. **Volume**: Volume spike confirmation

### Risk Management
- **Stop Loss**: 1.5x ATR from entry
- **Take Profit 1**: 2.5x ATR (25% position closes here)
- **Take Profit 2**: 4.0x ATR
- **Take Profit 3**: 6.0x ATR

### Position Management
- Maximum 3 open positions at once
- Only A+ setups are traded automatically
- A- setups generate alerts but require manual review
- Positions are closed when TP/SL is hit

## 🔔 Alert Examples

### Golden Pocket Proximity
```
🎯 APPROACHING GOLDEN POCKET - EUR/USD
Price is near Golden Pocket zone!
Current Price: $1.10500
GP Zone: $1.10450 - $1.10550
```

### A- Deviation Setup
```
📊 A- DEVIATION SETUP - GBP/USD
🟢 LONG Setup - A- Grade
Timeframe: 5m
Current Price: $1.25000
VWAP: $1.25200
Deviation: 1.85σ (2σ level)
```

### A+ Setup
```
⭐ A+ SETUP - USD/JPY
🔴 SHORT Setup - A+ Grade
Timeframe: 15m
Entry: $150.250
Stop Loss: $150.350
Take Profit 1: $150.100 (25%)
Take Profit 2: $150.000
Take Profit 3: $149.850
```

## 📝 Database

The bot uses SQLite to track:
- **Trades**: All open and closed positions
- **Account State**: Current balance and PnL

Database file: `forex_paper_trades.db`

## ⚙️ Configuration

Edit these settings in `forex_pivot_reversal_bot.py`:

```python
PAPER_TRADING_CONFIG = {
    "starting_balance": 1000.0,  # Starting balance
    "leverage": 150,              # Leverage multiplier
    "trade_size_usd": 50.0,       # Margin per trade
    "max_open_positions": 3,      # Max concurrent trades
    "tp1_percent": 25,            # % to close at TP1
}

SCAN_INTERVAL = 2700  # Seconds between scans (45 minutes)
```

## 🛠️ Technical Details

### Indicator Calculations
- **ATR**: 14-period Average True Range
- **VWAP**: Volume-Weighted Average Price (daily reset)
- **Standard Deviation**: Calculated from VWAP variance
- **Pivot Strength**: Dynamic based on ATR and timeframe

### Data Sources
- Uses `ccxt` library for exchange data
- Falls back to mock data if exchange unavailable (for testing)
- Supports OANDA, but can be configured for other forex brokers

## 📊 Performance Tracking

The bot tracks:
- Realized PnL
- Unrealized PnL
- Win/Loss ratio
- Daily PnL
- Open positions

## 🔒 Safety Features

- Maximum position limits
- Stop loss on all trades
- Partial profit taking (25% at TP1)
- Rate-limited alerts (prevents spam)
- Database persistence (survives restarts)

## 📚 Indicator References

- **PivotX Pro**: Based on `pivotx_pro_fixed.pine`
- **GPS**: Based on `gps_indicator_fixed.pine`
- **Tactical Deviation**: Based on `deviation_vwap_indicator.pine`

## 🎨 Discord Card Colors

- **Green (0x00FF00)**: Bullish/LONG setups
- **Purple (0x9B59B6)**: Bearish/SHORT setups
- **Gold (0xFFD700)**: Golden Pocket proximity (very close)
- **Orange (0xFFA500)**: Golden Pocket proximity (approaching)

---

**Note**: This is a paper trading bot for educational purposes. Always test thoroughly before using with real funds.


