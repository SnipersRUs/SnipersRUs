# 🚀 Railway + Bybit Trading Bot Deployment Guide

## Overview
This guide will help you deploy your Bybit trading bot to Railway, a modern cloud platform that makes deployment simple and scalable.

## 🎯 What You'll Get
- **REST API** for controlling your trading bot
- **Real-time monitoring** of trades and performance
- **Discord notifications** for trade alerts
- **Automatic scaling** and health monitoring
- **24/7 uptime** with Railway's infrastructure

## 📋 Prerequisites

### 1. Bybit Account Setup
1. Go to [Bybit.com](https://www.bybit.com) and create an account
2. Complete KYC verification
3. Go to **Account & Security** → **API Management**
4. Create a new API key with these permissions:
   - ✅ **Read** (for account info)
   - ✅ **Trade** (for placing orders)
   - ❌ **Withdraw** (not needed for trading bot)
5. Copy your **API Key** and **Secret Key**

### 2. Discord Webhook (Optional)
1. Go to your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Create a new webhook
4. Copy the webhook URL

### 3. Railway Account
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Connect your GitHub account

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository
1. **Fork or clone** this repository to your GitHub account
2. **Commit all files** to your repository
3. Make sure these files are in your repo root:
   - `app.py` (FastAPI server)
   - `bybit_exchange.py` (Bybit integration)
   - `bybit_config.py` (Configuration)
   - `bybit_golden_pocket_bot.py` (Trading bot)
   - `requirements.txt` (Dependencies)
   - `railway.json` (Railway config)
   - `Procfile` (Start command)

### Step 2: Deploy to Railway
1. Go to [Railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Railway will automatically detect it's a Python project

### Step 3: Configure Environment Variables
In your Railway project dashboard:

1. Go to **Variables** tab
2. Add these environment variables:

```bash
# Required: Bybit API Credentials
BYBIT_API_KEY=your_actual_api_key_here
BYBIT_API_SECRET=your_actual_secret_here

# Required: Trading Mode
BYBIT_TESTNET=true
BYBIT_PAPER_TRADING=true
BYBIT_LIVE_TRADING=false

# Optional: Discord Notifications
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook_url

# Optional: Telegram (if you want Telegram notifications)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Railway will set these automatically:
PORT=8000
RAILWAY_ENVIRONMENT=production
```

### Step 4: Deploy
1. Railway will automatically start building and deploying
2. Wait for the deployment to complete (usually 2-3 minutes)
3. Your bot will be available at: `https://your-project-name.railway.app`

## 🔧 API Endpoints

Once deployed, your bot API will be available at these endpoints:

### Core Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /status` - Bot status and statistics
- `GET /account` - Account information
- `GET /config` - Bot configuration

### Control Endpoints
- `POST /start` - Start the trading bot
- `POST /stop` - Stop the trading bot
- `POST /scan` - Run a single scan cycle
- `POST /test-connection` - Test Bybit connection

### Data Endpoints
- `GET /trades` - Get active trades
- `GET /symbols` - Get trading symbols
- `GET /market/{symbol}` - Get market data for symbol
- `GET /logs` - Get recent log entries

### Example API Usage

```bash
# Check if bot is running
curl https://your-project.railway.app/status

# Start the bot
curl -X POST https://your-project.railway.app/start

# Get account info
curl https://your-project.railway.app/account

# Run a scan
curl -X POST https://your-project.railway.app/scan
```

## 🛡️ Safety Features

### Paper Trading Mode (Default)
- **Default setting**: Paper trading enabled
- **No real money**: All trades are simulated
- **Safe testing**: Perfect for testing strategies

### Live Trading Mode
- **Manual activation**: Set `BYBIT_LIVE_TRADING=true`
- **Real money**: Trades with actual funds
- **Risk management**: Built-in safety limits

### Built-in Safety Limits
- **Max 3 concurrent trades**
- **2% risk per trade**
- **5% daily loss limit**
- **Emergency stop loss**
- **Cooldown periods**

## 📊 Monitoring & Alerts

### Discord Notifications
The bot sends real-time notifications for:
- ✅ **Trade executions**
- 🔒 **Trade closures**
- ❌ **Errors and issues**
- 📊 **Daily summaries**

### Railway Dashboard
Monitor your bot through Railway's dashboard:
- **Logs**: Real-time log streaming
- **Metrics**: CPU, memory, and network usage
- **Deployments**: Deployment history and rollbacks

## 🔄 Updating Your Bot

### Code Updates
1. **Push changes** to your GitHub repository
2. **Railway auto-deploys** the new version
3. **Zero downtime** deployments

### Configuration Updates
1. **Update environment variables** in Railway dashboard
2. **Redeploy** to apply changes
3. **Bot restarts** with new settings

## 🚨 Troubleshooting

### Common Issues

#### Bot Won't Start
```bash
# Check logs
curl https://your-project.railway.app/logs

# Test connection
curl -X POST https://your-project.railway.app/test-connection
```

#### API Connection Issues
- Verify your Bybit API credentials
- Check if API key has correct permissions
- Ensure you're using testnet for testing

#### Trading Issues
- Verify account has sufficient balance
- Check if symbols are available for trading
- Review risk management settings

### Getting Help
1. **Check Railway logs** in the dashboard
2. **Use the API** to get detailed status
3. **Review Discord notifications** for error messages

## 💰 Railway Pricing

### Free Tier
- **$5 credit** per month
- **500 hours** of usage
- **Perfect for testing** and small bots

### Pro Tier
- **$5/month** per service
- **Unlimited usage**
- **Better performance** and reliability

## 🎯 Next Steps

### 1. Test Your Deployment
```bash
# Test the API
curl https://your-project.railway.app/health

# Start paper trading
curl -X POST https://your-project.railway.app/start
```

### 2. Monitor Performance
- Watch Discord notifications
- Check Railway dashboard
- Review API status regularly

### 3. Go Live (When Ready)
1. **Test thoroughly** in paper mode
2. **Set `BYBIT_LIVE_TRADING=true`**
3. **Start with small position sizes**
4. **Monitor closely** for the first few days

## 🔐 Security Best Practices

### API Key Security
- ✅ **Use environment variables** (never hardcode)
- ✅ **Limit API permissions** (no withdraw access)
- ✅ **Use testnet** for development
- ✅ **Rotate keys regularly**

### Bot Security
- ✅ **Enable paper trading** by default
- ✅ **Set conservative limits**
- ✅ **Monitor all trades**
- ✅ **Use stop losses**

## 📈 Performance Optimization

### Railway Optimizations
- **Enable auto-scaling** for high traffic
- **Use Railway's CDN** for faster responses
- **Monitor resource usage** in dashboard

### Bot Optimizations
- **Adjust scan intervals** based on needs
- **Optimize symbol selection** for better performance
- **Use appropriate position sizes**

## 🎉 Congratulations!

You now have a fully deployed, production-ready trading bot running on Railway with Bybit integration! 

### What You Can Do Now:
- ✅ **Monitor trades** via API or Discord
- ✅ **Control the bot** remotely
- ✅ **Scale automatically** with Railway
- ✅ **Deploy updates** with zero downtime

### Support Resources:
- 📚 **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- 📚 **Bybit API Docs**: [bybit-exchange.github.io](https://bybit-exchange.github.io)
- 💬 **Discord**: Use your webhook for real-time updates

Happy trading! 🚀📈
