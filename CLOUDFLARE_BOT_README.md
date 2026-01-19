# Cloudflare Indicator Discord Bot

A Discord bot that receives TradingView webhook alerts from the Cloudflare indicator and sends optimized signals to Discord. Only processes signals for **BTC, SOL, and ETH**.

## Features

- ✅ **Symbol Filtering**: Only processes BTC, SOL, and ETH signals
- ✅ **Long/Short Signals**: Focuses on directional trading signals only
- ✅ **Smart Formatting**: Single signal = single card, multiple signals = combined card
- ✅ **Scheduled Scans**: Automatically scans markets every 45 minutes
- ✅ **Signal Types Detected**:
  - Master Long/Short signals
  - Bull/Bear confirmations
  - Divergence signals (bullish/bearish)
  - VWAP breaks (4D, Weekly)
  - Golden Cross / Death Cross
  - Liquidity flushes

## Setup

### 1. Install Dependencies

```bash
pip install flask requests
```

### 2. Configure Discord Webhook

The webhook URL is already configured in `cloudflare_discord_bot.py`:
```
https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS
```

### 3. Run the Bot

```bash
# Option 1: Direct Python
python3 cloudflare_discord_bot.py

# Option 2: Using the run script
./run_cloudflare_bot.sh
```

The bot will start on `http://localhost:5000`

## TradingView Alert Setup

### 1. Add Indicator to Chart

1. Open TradingView
2. Add the `cloudfare_accuracy_focused.pine` indicator to your BTC, SOL, or ETH chart
3. Configure the indicator settings as needed

### 2. Create Alerts

For each signal type you want to monitor, create an alert:

1. Click the "Alert" button on TradingView
2. Set condition to one of these alert conditions:
   - **Master Long Signal**
   - **Master Short Signal**
   - **Bull Confirmation**
   - **Bear Confirmation**
   - **Bullish Divergence**
   - **Bearish Divergence**
   - **Golden Cross**
   - **Death Cross**
   - **4D VWAP Break Above**
   - **4D VWAP Break Below**
   - **Weekly VWAP Break Above**
   - **Weekly VWAP Break Below**
   - **Liquidity Flush Bull**
   - **Liquidity Flush Bear**

3. In the alert settings:
   - **Webhook URL**: `http://YOUR_SERVER_IP:5000/webhook`
   - **Message**: Leave default (the bot will parse it)
   - **Frequency**: "Once Per Bar Close"

### 3. Deploy Bot Server

For production, deploy the bot to a server that's always online:

**Option A: Railway**
1. Create a Railway account
2. Connect your GitHub repo
3. Set the start command: `python3 cloudflare_discord_bot.py`
4. Railway will provide a public URL

**Option B: VPS/Cloud Server**
1. Deploy to AWS, DigitalOcean, etc.
2. Use `screen` or `tmux` to keep it running:
   ```bash
   screen -S cloudflare_bot
   python3 cloudflare_discord_bot.py
   ```

**Option C: Local with ngrok (for testing)**
```bash
# Terminal 1: Run bot
python3 cloudflare_discord_bot.py

# Terminal 2: Create tunnel
ngrok http 5000

# Use the ngrok URL in TradingView webhook
```

## Signal Format

### Single Signal
When one signal is received, it sends a single Discord embed with:
- Signal type and direction
- Symbol and price
- Timeframe
- Signal details

### Multiple Signals
If multiple signals arrive simultaneously, they're combined into one embed showing all signals grouped by symbol.

## API Endpoints

- `GET /` - Root endpoint with bot info
- `GET /health` - Health check
- `POST /webhook` - TradingView webhook endpoint

## Testing

Test the webhook with curl:

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "message": "🟢 MASTER LONG SIGNAL - HIGH ACCURACY",
    "price": "45000",
    "timeframe": "1h"
  }'
```

## Troubleshooting

### Bot not receiving alerts
1. Check bot is running: `curl http://localhost:5000/health`
2. Verify webhook URL in TradingView matches your server
3. Check bot logs for incoming requests

### Signals not appearing in Discord
1. Verify Discord webhook URL is correct
2. Check that symbol is BTC, SOL, or ETH
3. Ensure signal has a direction (LONG/SHORT)
4. Check bot logs for errors

### Symbol not recognized
The bot accepts these symbol formats:
- BTC, BITCOIN
- SOL, SOLANA
- ETH, ETHEREUM

Symbols are case-insensitive and can be part of pairs like "BTCUSDT".

## Notes

- **No Paper Trading**: This bot only sends signals, it does not execute trades
- **Signal Only**: Focuses on long/short signals only, ignores informational alerts
- **Real-time**: Processes signals immediately as they arrive via webhooks
- **Scheduled Scans**: Runs automatic market scans every 45 minutes to verify system health and check for signals

