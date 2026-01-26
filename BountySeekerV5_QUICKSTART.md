# Bounty Seeker v5 - Quick Start Guide

## 🚀 Quick Setup

1. **Install Dependencies** (if not already installed):
```bash
pip install ccxt numpy requests
```

2. **Set Discord Webhook** (optional - bot has default):
```bash
export DISCORD_WEBHOOK="your_webhook_url"
```

3. **Run the Bot**:
```bash
python3 bounty_seeker_v5.py
```

## 📋 What the Bot Does

### Every 5 Minutes:
- Scans all MEXC perpetual futures
- Looks for coins at 2σ/3σ deviation below VWAP
- Checks GPS proximity and liquidation zones
- Finds A/A+ grade long reversal setups
- Sends Discord alerts

### Signal Types:

**🟢 Green/White Alerts (Trade Signals):**
- A+ grade (9/10): 3σ deviation + GPS + Liquidation zone
- A grade (8/10): 2σ deviation + GPS or Liquidation zone
- Includes: Entry, Stop Loss, Take Profits, R:R ratio
- Educational explanations included

**🟠 Orange Alerts (Watchlist):**
- Top 3 coins approaching setup zones
- Shows distance to GPS
- Shows deviation level
- Monitor for potential A/A+ setups

**🔔 Exit Alerts:**
- When stop loss is hit (red)
- When take profit is hit (green)
- Shows PnL and updated balance

**📊 Daily PnL Report:**
- Sent once per day
- Total profit/loss
- Win rate
- Trade statistics

## ⚙️ Configuration

Edit `config.json`:
```json
{
  "AUTO_EXECUTE": false,
  "EXCHANGES": ["mexc"],
  "EXCLUDED_SYMBOLS": []
}
```

- **AUTO_EXECUTE:** `true` = auto-open paper trades, `false` = alerts only
- **EXCHANGES:** Currently only MEXC
- **EXCLUDED_SYMBOLS:** List symbols to exclude

## 💰 Paper Trading

- Starting capital: **$1,000**
- Max open trades: **3**
- Risk per trade: **2%** ($20)
- Leverage: **15x**
- Minimum R:R: **2:1**

## 📊 Understanding Signals

### Deviation VWAP:
- **2σ:** Price 2 standard deviations below VWAP (oversold)
- **3σ:** Price 3 standard deviations below VWAP (extremely oversold - rare!)

### GPS (Golden Pocket):
- Fibonacci retracement zone (61.8%-65%)
- Institutional support/resistance level
- Bot shows distance to GPS

### Liquidation Zones:
- Areas where large liquidations occurred
- Seller exhaustion = potential reversal
- Bot shows importance score

### RSI:
- **< 35:** Oversold (good for long reversals)
- Confirms oversold conditions

## 🎯 Strategy Summary

**What we're looking for:**
1. Coin trading 2σ or 3σ below VWAP (extreme oversold)
2. Near GPS or liquidation zone (confluence)
3. RSI < 35 (oversold confirmation)
4. Volume surge (seller exhaustion)
5. Large lower wick (rejection of lower prices)

**Why this works:**
- Extreme oversold = mean reversion opportunity
- GPS = institutional support level
- Liquidation zones = seller exhaustion
- Combined = high probability reversal setup

## ⚠️ Important Notes

- **Paper Trading Only** - Not real money
- **Always DYOR** - Do Your Own Research
- **NFA** - Not Financial Advice
- **Risk Management** - Never risk more than you can afford to lose

## 🔧 Troubleshooting

**No signals?**
- A/A+ setups are rare (quality over quantity)
- Check that MEXC is accessible
- Review logs for errors

**Alerts not sending?**
- Verify webhook URL
- Check internet connection
- Review error logs

**Trades not closing?**
- Bot checks every 5 minutes
- Verify exchange connection
- Check database for status

## 📝 Files

- `bounty_seeker_v5.py` - Main bot
- `data/bounty_seeker_v5_state.json` - State file
- `data/bounty_seeker_v5_trades.db` - Trade database
- `BountySeekerV5_README.md` - Full documentation

---

**Ready to start?** Run `python3 bounty_seeker_v5.py` and watch for Discord alerts! 🚀
