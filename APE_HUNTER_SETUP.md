# 🦍 APE HUNTER - DEGEN BOTTOM SNIPER

Your degen scanner for finding bottomed coins with volume sneaking in for potential moves!

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Set Discord Webhook (Optional but Recommended)
```bash
export DISCORD_WEBHOOK_URL="your_discord_webhook_url_here"
```

### 3. Run the Scanner

**Single Scan:**
```bash
python3 run_ape_hunter.py --scan
```

**Continuous Scanning (1.5h intervals):**
```bash
python3 run_ape_hunter.py --loop
```

**Custom Interval:**
```bash
python3 run_ape_hunter.py --loop --interval 3600  # 1 hour
```

## 🎯 What It Does

- **Scans 800+ MEXC spot-only coins** every 1.5 hours
- **Finds bottomed coins** with volume sneaking in
- **Top 5 picks** per scan with high conviction signals
- **Paper trading** with $10k starting balance
- **Max 3 open trades** at any time
- **Aggressive profit taking**: 10% (40% position), 40% (40% position), 100% (remaining)

## 📊 Strategy

### Entry Criteria
- **Drawdown**: -30% or more from recent high
- **RSI**: 25-45 (oversold)
- **Bollinger Band Width**: <0.12 (low volatility)
- **Volume**: Increasing vs 30-period average
- **24h Change**: <6% (calm price action)
- **Minimum Score**: 64/100

### Risk Management
- **Stop Loss**: 25% below entry
- **Take Profit 1**: 10% gain (close 40% of position, move stop to breakeven)
- **Take Profit 2**: 40% gain (close 40% of position, tighten stop to +10%)
- **Take Profit 3**: 100% gain (close remaining position)
- **Momentum Exit**: If price >40% and RSI <58 or price < EMA21

### Cooldown System
- **3 consecutive losses** → 1 hour cooldown
- **3 consecutive wins** → 1 hour cooldown
- **Entry gate**: Only open new trades after hitting TP1 or closing

## 📈 Paper Trading Features

- **Starting Balance**: $10,000
- **Position Size**: $500 base (15% larger for 90+ score signals)
- **State Persistence**: All trades and stats saved to `degen_sniper_state.json`
- **Real-time Updates**: Discord alerts for entries, exits, and status

## 🔧 Configuration

Edit `degen_config.py` to customize:
- Scan intervals
- Position sizes
- Risk parameters
- Volume filters
- Technical indicators

## 📱 Discord Integration

The scanner sends rich embeds to Discord with:
- **Entry alerts** when trades are opened
- **Take profit notifications** with realized P&L
- **Trade status updates** every scan
- **Watchlist** of potential movers
- **Performance stats** (W/L ratio, P&L)

## 🎮 Usage Examples

```bash
# Check configuration
python3 run_ape_hunter.py --config

# Single scan to see current opportunities
python3 run_ape_hunter.py --scan

# Run continuously (default 1.5h intervals)
python3 run_ape_hunter.py --loop

# Run with 1-hour intervals
python3 run_ape_hunter.py --loop --interval 3600

# Interactive mode (asks what you want to do)
python3 run_ape_hunter.py
```

## 📊 State File

The scanner maintains state in `degen_sniper_state.json`:
- Current paper trading balance
- Open trades with entry prices and stops
- Trade history with P&L
- Win/loss streaks and cooldown status

## ⚠️ Important Notes

- **Paper Trading Only**: This is for testing and analysis
- **High Risk**: DeFi tokens are extremely volatile
- **Not Financial Advice**: Use at your own risk
- **MEXC Only**: Scans MEXC spot markets exclusively
- **Rate Limited**: Respects MEXC API rate limits

## 🐛 Troubleshooting

**"MEXC connected" but no signals:**
- Market conditions may not meet criteria
- Check volume filters in config
- Try adjusting RSI bands or score thresholds

**Discord webhook not working:**
- Verify webhook URL is correct
- Check Discord server permissions
- Webhook will fallback to console output

**Scanner stops unexpectedly:**
- Check internet connection
- MEXC API may be temporarily unavailable
- Restart with `--loop` to resume

---

**Happy Hunting! 🦍💰**
