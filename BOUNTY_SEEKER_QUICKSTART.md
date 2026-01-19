# 🎯 Bounty Seeker - Quick Start Guide

## ✅ What's Been Created

1. **`bounty_seeker_bot.py`** - Main bot with all features
2. **`run_bounty_seeker.sh`** - Easy run script
3. **`BOUNTY_SEEKER_README.md`** - Full documentation

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
pip install ccxt numpy pandas requests
```

### Step 2: Run the Bot
```bash
python3 bounty_seeker_bot.py
```

Or:
```bash
./run_bounty_seeker.sh
```

### Step 3: Watch Discord
The bot will:
- Send a startup notification when it starts
- Scan markets at **XX:45** (15 minutes before each hour)
- Send **immediate alerts** when signals are found

## 📊 What the Bot Does

### Strategy
- **GPS Zones**: Golden Pocket (0.618-0.65 Fibonacci)
- **Deviation Bands**: 2.5σ - 3σ mean reversion
- **SFP Reversals**: Swing Failure Pattern detection
- **RSI Divergence**: Oversold conditions
- **Volume Confirmation**: Volume spikes

### Self-Learning
- Tracks all trades (wins/losses)
- Adjusts minimum confidence based on performance
- Weights strategy components (GPS, SFP) by success rate
- Gets smarter with every trade

### Discord Alerts
- **Immediate notifications** when signals found
- Green card style matching your HTML design
- Includes: Entry, Stop Loss, Take Profit, Confidence Score, Reasons

## ⏰ Scanning Schedule

The bot scans at **XX:45 UTC** (15 minutes before each hour):
- 00:45, 01:45, 02:45, ... 23:45
- Checks every minute for the 45th minute
- Sends alerts immediately when signals are found

## 📈 Example Signal

When a signal is found, you'll get a Discord message like:

```
BTC/USDT // REVERSAL ALERT
Targeting local bottom for mean reversion bounce.

ENTRY: $63,450.00
STOP LOSS: $62,815.50
TAKE PROFIT: $65,036.25
CONFIDENCE: 85/100
RSI: 28.5
DEVIATION: -2.8σ

Why This Trade?
✅ Deviation Zone -2.5 Sigma (Mean Reversion)
✅ Price in Daily Golden Pocket (0.618-0.65)
✅ RSI Oversold (28.5)
✅ SFP Reversal Detected (Sweeping Lows)
✅ Volume Spike (2.1x average)
```

## 🎯 Trading Parameters

- **Target**: 2.5% profit (2-3% range)
- **Stop Loss**: 1.0%
- **Risk:Reward**: 2.5:1
- **Minimum Confidence**: 70/100 (auto-adjusts)

## 📁 Data Files

The bot creates:
- `data/bounty_seeker_trades.db` - Trade history
- `data/bounty_seeker_learning.db` - Learning data
- `data/bounty_seeker_state.json` - Bot state
- `bounty_seeker.log` - Log file

## 🔧 Configuration

Edit these in `bounty_seeker_bot.py`:

```python
MIN_CONFIDENCE_SCORE = 70  # Minimum to trigger
TARGET_PROFIT_PCT = 2.5  # Target gain %
STOP_LOSS_PCT = 1.0  # Stop loss %
DEVIATION_2SIGMA = 2.5  # 2.5σ threshold
DEVIATION_3SIGMA = 3.0  # 3σ threshold
```

## 🧠 Self-Learning Details

The bot learns from every trade:
1. Records outcome (win/loss, P&L, confidence)
2. Analyzes last 50 trades
3. Adjusts parameters:
   - Win rate < 50% → Raise minimum confidence
   - Win rate > 70% → Lower minimum confidence
   - GPS/SFP weights based on component success

## ⚠️ Important Notes

- **Signal Generation Only**: Bot sends alerts, you execute trades
- **No Auto-Trading**: Manual execution required
- **Paper Trading Ready**: Can be extended for live trading
- **Learning Period**: Needs 10+ trades to start learning effectively

## 🐛 Troubleshooting

### Bot not scanning?
- Check logs: `tail -f bounty_seeker.log`
- Verify it's XX:45 UTC
- Check exchange connection

### No Discord alerts?
- Verify webhook URL in code
- Check Discord server permissions
- Test webhook with a simple POST request

### Import errors?
```bash
pip install --upgrade ccxt numpy pandas requests
```

## 📞 Next Steps

1. **Run the bot** and let it scan
2. **Monitor Discord** for alerts
3. **Track performance** in the database
4. **Review logs** for insights
5. **Adjust parameters** based on results

---

**Ready to hunt for bounties! 🎯**
