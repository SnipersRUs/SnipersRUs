# Bounty Seeker v5 - Reversal Hunter Bot

## 🎯 Strategy Overview

**Bounty Seeker v5** is a specialized trading bot designed to find **long reversal opportunities** at market bottoms. It focuses on identifying coins where **sellers are exhausted** and price is ready to bounce.

### Core Strategy Components:

1. **Deviation VWAP Analysis** - Finds coins trading 2σ or 3σ below VWAP (extreme oversold conditions)
2. **Liquidation Zone Detection** - Identifies areas where large liquidations occurred (15m, 1h, 4h, daily)
3. **GPS (Golden Pocket) Proximity** - Tracks distance to Golden Pocket levels (61.8%-65% Fibonacci retracement)
4. **Seller Exhaustion Signals** - Detects large lower wicks, volume spikes, and RSI oversold conditions

## 📊 Signal Quality - A and A+ Only

The bot **ONLY** trades **A grade (8/10)** and **A+ grade (9/10)** setups. No B trades.

### A Grade Requirements (8/10):
- Price at 2σ deviation below VWAP
- Near GPS or liquidation zone
- RSI < 35 (oversold)
- Volume confirmation
- Seller exhaustion signals

### A+ Grade Requirements (9/10):
- Price at **3σ deviation** below VWAP (extreme oversold)
- Near GPS **AND** liquidation zone
- RSI < 35
- Strong volume surge (>1.5x average)
- Large lower wick (seller exhaustion)

## 💰 Paper Trading

- **Starting Capital:** $1,000
- **Max Open Trades:** 3 positions
- **Risk per Trade:** 2% of capital
- **Leverage:** 15x
- **Minimum R:R:** 2:1 (targets: 2:1, 3:1, 4.5:1)

## 🔔 Discord Alerts

### Signal Colors:
- **🟢 Green:** A+ grade trade signals (highest quality)
- **⚪ White:** A grade trade signals (high quality)
- **🟠 Orange:** Watchlist alerts (3 coins approaching setup zones)

### Alert Types:

1. **Trade Signals** - When A/A+ setup is detected
   - Entry price, stop loss, take profit levels
   - Risk:Reward ratio
   - Educational explanations
   - TradingView chart link

2. **Watchlist Alerts** - Top 3 coins approaching deviation/liquidation zones
   - Shows distance to GPS
   - Deviation level
   - Liquidation zone proximity

3. **Trade Exit Alerts** - When stop loss or take profit is hit
   - Exit reason (Stop Loss, TP1, TP2, TP3)
   - PnL (profit/loss)
   - Updated balance

4. **Daily PnL Report** - Sent once per day
   - Total PnL
   - Win rate
   - Trade statistics

## 📈 Indicators Explained

### Deviation VWAP (2σ/3σ)
- **What it is:** VWAP (Volume Weighted Average Price) with standard deviation bands
- **2σ Deviation:** Price is 2 standard deviations below VWAP (oversold)
- **3σ Deviation:** Price is 3 standard deviations below VWAP (extremely oversold - rare event)
- **Why it matters:** Statistical mean reversion - prices tend to return to VWAP after extreme deviations

### GPS (Golden Pocket)
- **What it is:** Fibonacci retracement zone between 61.8% and 65%
- **Why it matters:** This is where institutional traders often place orders. Price often reverses here.
- **Distance tracking:** Bot shows how far price is from GPS (closer = better)

### Liquidation Zones
- **What it is:** Areas where large liquidations occurred (high volume + large wicks)
- **Why it matters:** After liquidations, price often reverses as sellers are exhausted
- **Importance score:** Higher score = more significant liquidation event

### RSI (Relative Strength Index)
- **What it is:** Momentum oscillator (0-100)
- **Oversold:** RSI < 35 (price may bounce)
- **Why it matters:** Confirms oversold conditions for reversal trades

## 🎓 Educational Notes

The bot includes educational explanations in every alert to help new traders understand:

- **Why this setup is good:** Explains the confluence factors
- **What to watch for:** Key levels and indicators
- **Risk management:** Stop loss and take profit placement
- **Market context:** What the indicators mean

## ⚙️ Configuration

### Environment Variables:
```bash
export DISCORD_WEBHOOK="your_webhook_url"
```

### Config File (`config.json`):
```json
{
  "AUTO_EXECUTE": false,
  "EXCHANGES": ["mexc"],
  "EXCLUDED_SYMBOLS": []
}
```

- **AUTO_EXECUTE:** Set to `true` to automatically open paper trades (default: `false`)
- **EXCHANGES:** Currently only MEXC perpetual futures
- **EXCLUDED_SYMBOLS:** List of symbols to exclude from scanning

## 📁 Files Created

- `data/bounty_seeker_v5_state.json` - Bot state and paper balance
- `data/bounty_seeker_v5_trades.db` - SQLite database with all trades
- `bounty_seeker_v5.py` - Main bot script

## 🚀 Running the Bot

```bash
# Make executable
chmod +x bounty_seeker_v5.py

# Run directly
python3 bounty_seeker_v5.py

# Or with environment variable
DISCORD_WEBHOOK="your_webhook" python3 bounty_seeker_v5.py
```

## 📊 Trade Tracking

All trades are logged to SQLite database with:
- Entry/exit prices
- PnL (profit/loss)
- Exit reason
- Grade and confidence
- Reasons for entry

## ⚠️ Important Disclaimers

- **Paper Trading Only:** This bot uses paper trading (simulated capital)
- **Not Financial Advice:** Always DYOR (Do Your Own Research)
- **Risk Warning:** Trading involves risk. Never trade with money you can't afford to lose
- **Educational Purpose:** This bot is for educational purposes to learn about trading strategies

## 🔧 Troubleshooting

### Bot not finding signals?
- Check that MEXC exchange is accessible
- Verify symbols are active perpetual futures
- Lower confidence threshold (not recommended - stick to A/A+ only)

### Discord alerts not sending?
- Verify webhook URL is correct
- Check internet connection
- Review logs for error messages

### Trades not closing?
- Bot checks exits every scan (5 minutes)
- Verify current price is accessible from exchange
- Check database for trade status

## 📝 Notes for New Traders

1. **Start with Paper Trading:** Always test strategies with paper trading first
2. **Understand the Setup:** Read the educational notes in each alert
3. **Risk Management:** Never risk more than 2% per trade
4. **Patience:** A/A+ setups are rare - quality over quantity
5. **Learn:** Study why each setup worked or didn't work

## 🎯 Key Concepts

### Why Long at Bottoms?
- When sellers are exhausted, there's less selling pressure
- Price often bounces from extreme oversold levels
- Mean reversion - price returns to average

### Why Deviation VWAP?
- Shows where price is relative to average trading price
- 2σ/3σ deviations are statistically rare events
- High probability of mean reversion

### Why GPS?
- Institutional support/resistance level
- High confluence area
- Often where reversals occur

### Why Liquidation Zones?
- After liquidations, sellers are exhausted
- Price often reverses
- Creates support/resistance levels

---

**Remember:** Always DYOR - Not Financial Advice (NFA)

If you have questions, feel free to ask in chat or consult your AI trading assistant!
