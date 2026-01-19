# Bounty Seeker Bot 🎯

A sophisticated reversal trading bot that catches bottoms and tops using Elliott Wave 3 pullbacks with multiple indicator confluence.

## Features

### Indicators Integrated
1. **GPS (Golden Pocket Syndicate)** - Detects optimal entry zones at 0.618-0.65 Fibonacci retracement levels
2. **Oath Keeper** - Detects macro divergences (white circle prints) for reversal signals
3. **SFP (Smart Fibonacci Points)** - 3-level confluence detection across 15m, 1h, and 4h timeframes
4. **Mini VWAPs** - Trend analysis using VWAP stacking:
   - Bullish: 1H < 4H < Daily
   - Bearish: 1H > 4H > Daily
5. **Elliott Wave 3 Pullback** - ABC correction pattern detection

### Trading Rules
- **Paper Trading**: Starts with $1,000
- **Max Open Trades**: 3 trades at once (until TP1 is hit)
- **Take Profit 1**: 1.75% (aggressive, between 1.5-2%)
- **Take Profit 2**: 3%
- **Stop Loss**: Max 3% loss
- **Leverage**: 15x on all trades
- **Position Size**: $100 per trade (with 15x = $1,500 exposure)
- **No Repeat Entries**: If a trade fails, move on to next coin

### Market Scanning
- **Exchange**: MEXC Futures
- **Timeframes**: 15m, 1h, 4h (focus on 15min+)
- **Volume Filter**: Minimum $500k 24h volume (excludes dead coins)
- **Max Signals**: 3 signals per hour scan
- **Watchlist**: 3 coins on standby (orange cards)

### Discord Notifications
- **Long Trades**: Green cards 🟢
- **Short Trades**: Purple cards 🟣
- **Watchlist**: Orange cards 🟠
- **SFP Approaching**: Gold notifications 🔔
- **PNL Updates**: After each trade closes (last 10 trades)
- **Detailed Explanations**: Every card explains why the trade is being taken

## Setup

1. **Install Dependencies**:
```bash
pip install ccxt pandas numpy requests
```

2. **Configure Discord Webhook**:
   - The webhook is already configured in the bot
   - Webhook: `https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr`

3. **Run the Bot**:
```bash
chmod +x run_bounty_seeker.sh
./run_bounty_seeker.sh
```

Or directly:
```bash
python3 bounty_seeker_bot.py
```

## How It Works

### Signal Generation
1. **GPS Touch**: Price must be at or near Golden Pocket zone (0.618-0.65)
2. **Confluence Requirements**:
   - Minimum 55/100 confluence score
   - Must have at least 2 of: Oath Keeper divergence, SFP levels (≥2), or Wave 3 pullback
3. **Trend Alignment**: VWAP stack must not be fighting the trade direction
4. **SFP Levels**: Prefers 3-level confluence (15m, 1h, 4h)

### Trade Management
- **Entry**: Market price when signal is generated
- **TP1**: Aggressive 1.75% target (taken quickly)
- **TP2**: 3% target (if TP1 is hit, can continue to TP2)
- **Stop Loss**: 3% max loss
- **Position Sizing**: $100 base with 15x leverage = $1,500 exposure

### Risk Management
- Maximum 3 trades open simultaneously
- No repeat entries on failed trades
- Automatic stop loss at 3%
- PNL tracking and reporting

## Database

The bot uses SQLite database (`bounty_seeker_trades.db`) to store:
- Account state (balance, stats)
- All trades (entry, exit, P&L)
- Failed trades (to avoid repeat entries)

## Logs

Bot logs to both:
- Console output
- `bounty_seeker.log` file

## Discord Card Examples

### Long Trade Card (Green)
```
🎯 Bounty Seeker Signal: BTC/USDT LONG
Entry: $43,250.00
Confluence: 75/100
Why This Trade?
✅ Price at Golden Pocket zone (0.618-0.65)
✅ Macro divergence detected (Oath Keeper white circle)
✅ SFP 3-level confluence: 3 levels (15m, 1h, 4h)
✅ Bullish VWAP stack (1H < 4H < Daily)
```

### Short Trade Card (Purple)
```
🎯 Bounty Seeker Signal: ETH/USDT SHORT
Entry: $2,450.00
Confluence: 70/100
Why This Trade?
✅ Price at Golden Pocket zone (0.618-0.65)
✅ SFP confluence: 2 levels
✅ Elliott Wave 3 pullback detected (ABC correction)
✅ Bearish VWAP stack (1H > 4H > Daily)
```

### Watchlist Card (Orange)
```
👀 Watchlist: SOL/USDT
Approaching GPS zone (1.25% away)
```

### SFP Notification (Gold)
```
🔔 SFP Approaching: AVAX/USDT
Price is approaching Smart Fibonacci Point
15m BULLISH SFP
Mid: $38.50 (0.75% away)
```

## Monitoring

The bot:
- Scans every 60 minutes (1 hour)
- Updates active trades continuously
- Sends PNL updates after each trade closes
- Tracks last 10 trades in Discord updates

## Notes

- The bot focuses on **quality over quantity** - max 3 signals per hour
- **Higher timeframes = better reversals** (as per your requirements)
- **No fighting the trend** - VWAP stack must align
- **Dead coins filtered out** - minimum volume requirement
- **SFP notifications** alert you to potential setups before they trigger

## Troubleshooting

1. **No signals**: Check volume filter, may need to lower `MIN_VOLUME_24H_USD`
2. **Database errors**: Delete `bounty_seeker_trades.db` to reset
3. **Discord not working**: Check webhook URL
4. **MEXC connection issues**: Check internet connection and MEXC API status

## Future Enhancements

- Add more sophisticated Elliott Wave detection
- Implement additional confluence factors
- Add backtesting capabilities
- Real-time position monitoring dashboard


