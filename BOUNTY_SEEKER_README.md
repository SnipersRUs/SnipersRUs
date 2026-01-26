# 🎯 Bounty Seeker - Reversal Sniper Bot

**Pure Bottom Finder for Reversal Trades | Targeting 2-3% Gains**

## 📋 Overview

Bounty Seeker is an intelligent trading bot that scans crypto perpetual futures markets to find high-probability reversal opportunities at support levels. The bot uses a multi-factor scoring system to identify "almost sure" bottoms for mean reversion trades.

## 🎯 Strategy Components

### 1. **GPS Zones (Golden Pocket)**
- Fibonacci retracement between 0.618 - 0.65
- Daily range analysis
- High-probability reversal zones

### 2. **Deviation Bands (Mean Reversion)**
- VWAP-based standard deviation
- Targets 2.5σ - 3σ oversold conditions
- Statistical mean reversion opportunities

### 3. **SFP Reversals (Swing Failure Pattern)**
- Detects liquidity sweeps
- Lower wick rejections
- Price structure reversals

### 4. **RSI Divergence**
- Oversold conditions (25-35 RSI)
- Bullish divergence detection
- Momentum confirmation

### 5. **Volume Confirmation**
- Volume spikes (1.5x+ average)
- Real buying interest validation

## 🧠 Self-Learning System

The bot automatically adjusts parameters based on performance:

- **Win Rate Analysis**: Tracks win/loss ratios
- **Confidence Adjustment**: Raises minimum confidence if win rate drops
- **Strategy Weighting**: Adjusts GPS and SFP importance based on success rates
- **Performance Tracking**: Records all trades for continuous improvement

### Learning Features:
- Analyzes last 50 trades
- Adjusts minimum confidence threshold
- Weights strategy components (GPS, SFP) based on performance
- Records trade outcomes for pattern recognition

## 📊 Exchange & Markets

**Exchange**: Binance Futures (Best Liquidity)
- $15-20B+ daily volume
- Tightest spreads
- 200+ USDT-M perpetuals
- Excellent order book depth

**Monitored Symbols** (24 top liquid pairs):
- BTC, ETH, SOL, BNB, XRP, ADA, AVAX, DOGE
- TRX, LINK, MATIC, DOT, UNI, LTC, ATOM, ETC
- ARB, OP, SUI, APT, INJ, TIA, SEI, WLD

## ⏰ Scanning Schedule

**Scan Time**: XX:45 UTC (15 minutes before the hour)
- Bot checks every minute
- Triggers scan at 45th minute
- Sends alerts immediately when signals found

## 📈 Trading Parameters

- **Target Profit**: 2.5% (2-3% range)
- **Stop Loss**: 1.0%
- **Risk:Reward**: 2.5:1
- **Minimum Confidence**: 70/100 (adjusts based on learning)
- **Cooldown**: 5 minutes per symbol

## 🔔 Discord Notifications

The bot sends immediate Discord webhook alerts when signals are found:

- **Entry Price**: Exact entry point
- **Stop Loss**: Risk management level
- **Take Profit**: Target level
- **Confidence Score**: Signal quality (0-100)
- **Reasons**: Detailed explanation of why the trade was triggered
- **Technical Indicators**: RSI, Deviation, GPS status

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables (Optional)
```bash
export BINANCE_API_KEY="your_key"  # Optional, for live trading
export BINANCE_SECRET="your_secret"  # Optional
```

### 3. Run the Bot
```bash
python3 bounty_seeker_bot.py
```

Or use the run script:
```bash
./run_bounty_seeker.sh
```

## 📁 Data Storage

The bot creates the following files:

- `data/bounty_seeker_trades.db` - Trade history
- `data/bounty_seeker_learning.db` - Learning system data
- `data/bounty_seeker_state.json` - Bot state
- `bounty_seeker.log` - Log file

## 🔧 Configuration

Edit the configuration section in `bounty_seeker_bot.py`:

```python
# Trading Parameters
MIN_CONFIDENCE_SCORE = 70  # Minimum score to trigger
TARGET_PROFIT_PCT = 2.5  # Target 2-3% gains
STOP_LOSS_PCT = 1.0  # 1% stop loss

# Technical Parameters
DEVIATION_2SIGMA = 2.5  # 2.5σ threshold
DEVIATION_3SIGMA = 3.0  # 3σ threshold
GPS_LOW = 0.618  # Golden Pocket low
GPS_HIGH = 0.65  # Golden Pocket high
```

## 📊 Signal Scoring System

Signals are scored from 0-100:

- **Deviation Zone -3σ**: +40 points
- **Deviation Zone -2.5σ**: +30 points
- **GPS Zone**: +30 points (weighted by learning)
- **RSI Oversold (25-35)**: +20 points
- **RSI Extreme (<30)**: +10 points
- **SFP Reversal**: +10 points (weighted by learning)
- **Volume Spike (1.5x+)**: +10 points

**Minimum Score**: 70 (adjusts based on performance)

## 🎯 Example Signal

```
🎯 BOUNTY FOUND // BTC/USDT
Reversal Alert - Targeting local bottom for mean reversion bounce

📊 Entry: $63,450.00
🛑 Stop Loss: $62,815.50
🎯 Take Profit: $65,036.25
⭐ Confidence Score: 85/100
📈 RSI: 28.5
📉 Deviation: -2.8σ

✅ Why This Trade?
• Deviation Zone -2.5 Sigma (Mean Reversion)
• Price in Daily Golden Pocket (0.618-0.65)
• RSI Oversold (28.5)
• SFP Reversal Detected (Sweeping Lows)
• Volume Spike (2.1x average)
```

## 🧠 Learning System Details

The bot learns from every trade:

1. **Records Trade Outcomes**: Entry, exit, P&L, confidence, reasons
2. **Analyzes Performance**: Win rate, average P&L, strategy component success
3. **Adjusts Parameters**:
   - Raises minimum confidence if win rate < 50%
   - Lowers minimum confidence if win rate > 70%
   - Adjusts GPS/SFP weights based on component win rates
4. **Continuous Improvement**: Gets smarter with every trade

## ⚠️ Important Notes

- **Paper Trading**: Currently configured for signal generation only
- **No Auto-Execution**: Bot sends alerts, you execute trades
- **Risk Management**: Always use stop losses
- **Market Conditions**: Best in ranging/sideways markets
- **Learning Period**: Bot needs 10+ trades to start learning effectively

## 📝 Logging

The bot logs all activity to `bounty_seeker.log`:
- Scan times
- Signals found
- Discord notifications
- Learning adjustments
- Errors and warnings

## 🔄 Updates & Improvements

The bot continuously improves through:
- Self-learning parameter adjustments
- Performance-based strategy weighting
- Trade outcome analysis
- Pattern recognition

## 📞 Support

For issues or questions:
- Check logs: `tail -f bounty_seeker.log`
- Review database: `sqlite3 data/bounty_seeker_trades.db`
- Verify Discord webhook: Test with a simple POST request

---

**Happy Hunting! 🎯**
