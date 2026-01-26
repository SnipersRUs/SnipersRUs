# 🚀 Ultimate Scalper Bot - Phemex Integration

A high-frequency scalping bot designed to capture 1-2% moves with 3-4 trades per day, built on your Bounty Seeker v4 architecture.

## 🎯 Features

### Core Scalping Features
- **High-Frequency Scanning**: 30-second intervals for quick opportunities
- **1-2% Profit Targets**: Optimized for quick scalping moves
- **Tight Risk Management**: 0.8% stop loss, 1.5% take profit
- **Daily Trade Limits**: Maximum 4 trades per day
- **Position Sizing**: $100 per trade with 10x leverage
- **Paper Trading**: Safe testing mode enabled by default

### Technical Analysis
- **RSI Analysis**: Oversold/overbought conditions
- **EMA Crossovers**: 5/10 EMA for quick signals
- **Volume Spikes**: 2x average volume detection
- **Price Momentum**: 1-minute and 5-minute momentum
- **Multi-Symbol**: 12 high-liquidity pairs

### Risk Management
- **Daily Loss Limit**: $200 maximum daily loss
- **Position Limits**: Maximum 2% of balance per trade
- **Cooldown Periods**: 5-minute cooldown between trades
- **Confidence Scoring**: Minimum 6/10 confidence required

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install ccxt pandas numpy requests
```

### 2. Configure API Keys
Your Phemex API credentials are already configured:
- **API Key**: `2c213e33-e1bd-44ac-bf9a-44a4cd2e065a`
- **Secret**: `4Q2dti8eGbr-QeADqpGA1n6hSs9K4Fb7PPNOeYUkQHhlNTg1NzdiMy0yNjkyLTRiNjEtYWU2ZS05OTA5YjljYzQ2MTc`
- **IP Whitelist**: `162.233.183.68`

### 3. Test the Bot
```bash
# Run comprehensive tests
python3 test_scalper_bot.py

# Run live test (5 minutes)
python3 test_scalper_bot.py --live
```

### 4. Start Trading
```bash
# Start the scalper bot
python3 run_scalper.py
```

## 📊 Configuration

### Trading Parameters
```json
{
  "TARGET_PROFIT_PCT": 1.5,      // 1.5% profit target
  "STOP_LOSS_PCT": 0.8,          // 0.8% stop loss
  "POSITION_SIZE_USDT": 100,     // $100 per trade
  "LEVERAGE": 10,                 // 10x leverage
  "MAX_DAILY_TRADES": 4,          // Max 4 trades per day
  "SCAN_INTERVAL_SEC": 30         // 30-second scans
}
```

### Risk Management
```json
{
  "MAX_DAILY_LOSS_USDT": 200,    // $200 daily loss limit
  "MAX_POSITION_SIZE_PCT": 2.0,  // 2% max position size
  "MIN_CONFIDENCE_SCORE": 6,     // Minimum 6/10 confidence
  "COOLDOWN_BETWEEN_TRADES_SEC": 300  // 5-minute cooldown
}
```

## 🎯 Trading Strategy

### Signal Detection
The bot looks for:

1. **EMA Crossovers**: 5/10 EMA bullish/bearish crosses
2. **RSI Extremes**: Oversold (<35) or overbought (>65)
3. **Volume Spikes**: 2x average volume
4. **Price Momentum**: Quick 1-minute moves
5. **Confluence**: Multiple signals aligning

### Entry Conditions
- **Long**: EMA bullish cross + price above EMA5 + volume spike
- **Short**: EMA bearish cross + price below EMA5 + volume spike
- **Confidence**: Minimum 6/10 required
- **Volume**: Must be 2x average volume

### Exit Strategy
- **Take Profit**: 1.5% profit target
- **Stop Loss**: 0.8% stop loss
- **Time Limit**: No time-based exits (scalping focus)

## 📈 Performance Tracking

### Daily Statistics
- **Trades Today**: Number of trades executed
- **Profit Today**: Daily P&L tracking
- **Win Rate**: Success rate monitoring
- **Drawdown**: Maximum loss tracking

### Discord Alerts
Real-time notifications for:
- ⚡ New scalping signals
- 🎯 Trade executions
- 📊 Daily performance
- ❌ Error alerts

## 🛡️ Safety Features

### Paper Trading Mode
- **Default**: Always starts in paper trading
- **Simulation**: Realistic order simulation
- **No Risk**: No real money at risk
- **Easy Switch**: Simple config change to go live

### Risk Controls
- **Daily Limits**: Maximum 4 trades per day
- **Loss Limits**: $200 daily loss limit
- **Position Sizing**: Automatic position calculation
- **Cooldowns**: 5-minute breaks between trades

## 🔧 Advanced Configuration

### Symbol Selection
```python
SCALPING_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
    "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT",
    "MATIC/USDT", "DOT/USDT", "LINK/USDT", "UNI/USDT"
]
```

### Technical Parameters
```python
SCALPING_PARAMS = {
    "RSI_OVERSOLD": 35,           // RSI oversold level
    "RSI_OVERBOUGHT": 65,         // RSI overbought level
    "VOLUME_SPIKE_THRESHOLD": 2.0, // 2x volume spike
    "PRICE_MOMENTUM_THRESHOLD": 0.3, // 0.3% momentum
    "EMA_FAST_PERIOD": 5,        // Fast EMA period
    "EMA_SLOW_PERIOD": 10         // Slow EMA period
}
```

## 📱 Monitoring

### Discord Integration
- **Webhook**: Already configured
- **Alerts**: Real-time trade notifications
- **Performance**: Daily summaries
- **Errors**: System error alerts

### Logging
- **Comprehensive**: All activities logged
- **Performance**: Trade statistics
- **Errors**: Full error tracking
- **Audit**: Complete trading history

## 🚨 Important Notes

### Before Going Live
1. **Test Thoroughly**: Run paper trading for at least a week
2. **Monitor Performance**: Track win rate and drawdown
3. **Adjust Parameters**: Fine-tune based on results
4. **Start Small**: Begin with smaller position sizes
5. **Monitor Markets**: Watch for unusual market conditions

### Risk Warnings
- **High Frequency**: 30-second scans can be intense
- **Leverage Risk**: 10x leverage amplifies both gains and losses
- **Market Risk**: Cryptocurrency markets are highly volatile
- **Technical Risk**: Ensure stable internet and power

## 🔄 Running the Bot

### Development Mode
```bash
# Paper trading with detailed logs
python3 run_scalper.py
```

### Production Mode
1. Set `"PAPER_TRADING": false` in config
2. Ensure API keys are configured
3. Start the bot:
```bash
python3 run_scalper.py
```

### Background Running
```bash
# Run in background
nohup python3 run_scalper.py > scalper.log 2>&1 &

# Or use screen
screen -S scalper
python3 run_scalper.py
# Ctrl+A, D to detach
```

## 📊 Expected Performance

### Daily Targets
- **Trades**: 3-4 trades per day
- **Profit**: 1-2% per trade
- **Win Rate**: 60-70% target
- **Daily P&L**: $150-300 target

### Risk Management
- **Max Daily Loss**: $200
- **Position Size**: $100 per trade
- **Leverage**: 10x
- **Stop Loss**: 0.8%

## 🎉 Success Metrics

### Key Performance Indicators
- **Daily Profit**: Track daily P&L
- **Win Rate**: Monitor success rate
- **Drawdown**: Track maximum losses
- **Trade Frequency**: Monitor trade count
- **Risk-Adjusted Returns**: Sharpe ratio

### Optimization
- **Parameter Tuning**: Adjust based on performance
- **Symbol Selection**: Focus on best performers
- **Time Optimization**: Identify best trading hours
- **Market Conditions**: Adapt to volatility

## 🚀 Next Steps

1. **Test Extensively**: Run paper trading for 1-2 weeks
2. **Monitor Performance**: Track all metrics
3. **Optimize Parameters**: Fine-tune based on results
4. **Scale Gradually**: Start small and increase
5. **Stay Updated**: Keep bot and dependencies updated

Happy Scalping! 🚀⚡

---

**Remember**: This is a high-frequency trading bot. Always test thoroughly in paper trading mode before using real money. Cryptocurrency trading involves significant risk.







