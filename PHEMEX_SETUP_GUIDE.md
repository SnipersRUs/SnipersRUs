# Phemex Trading Bot Setup Guide

This guide will help you set up a comprehensive trading bot for Phemex exchange, integrated with your existing trading infrastructure.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Phemex account with API access
- Basic understanding of trading concepts

### 2. Installation

```bash
# Install required dependencies
pip install ccxt pandas numpy asyncio aiohttp

# Or install from requirements
pip install -r requirements.txt
```

### 3. Configuration

1. **Get Phemex API Credentials:**
   - Log into your Phemex account
   - Go to Account → API Management
   - Create a new API key with trading permissions
   - Copy your API Key and Secret

2. **Configure the Bot:**
   ```bash
   # Edit phemex_config.py
   nano phemex_config.py
   ```

   Update these settings:
   ```python
   PHEMEX_CONFIG = {
       'apiKey': 'YOUR_ACTUAL_API_KEY',
       'secret': 'YOUR_ACTUAL_SECRET_KEY',
       'sandbox': True,  # Start with sandbox mode
       'options': {
           'defaultType': 'swap',  # or 'spot'
           'test': True  # Set to False for live trading
       }
   }
   ```

3. **Set Discord Webhook (Optional):**
   ```python
   PHEMEX_NOTIFICATION_CONFIG = {
       'discord_webhook': 'YOUR_DISCORD_WEBHOOK_URL',
       # ... other settings
   }
   ```

## 🧪 Testing

### Paper Trading Test
```bash
# Run the test suite
python test_phemex_bot.py
```

This will test:
- ✅ Connection to Phemex
- ✅ Market data fetching
- ✅ Order placement simulation
- ✅ Position management
- ✅ Trading bot functionality

### Manual Testing
```bash
# Start the bot in paper trading mode
python phemex_trading_bot.py
```

## 📊 Features

### Core Trading Features
- **Multi-symbol trading**: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX
- **Leverage management**: Symbol-specific leverage limits
- **Risk management**: Stop loss, take profit, position sizing
- **Technical analysis**: RSI, EMA, volume analysis
- **Real-time monitoring**: Live price updates and position tracking

### Advanced Features
- **Paper trading**: Test strategies without real money
- **Signal generation**: Automated buy/sell signals
- **Position management**: Automatic stop loss and take profit
- **Performance tracking**: P&L, win rate, trade statistics
- **Discord integration**: Real-time alerts and notifications

## 🔧 Configuration Options

### Trading Configuration
```python
PHEMEX_TRADING_CONFIG = {
    'max_risk_per_trade': 0.05,      # 5% max risk per trade
    'max_daily_loss': 0.10,          # 10% max daily loss
    'max_open_positions': 3,         # Maximum concurrent positions
    'base_position_size': 100.0,     # Base position size in USDT
    'default_leverage': 10,          # Default leverage
    'symbol_leverage': {             # Symbol-specific leverage
        'BTC/USDT': 20,
        'ETH/USDT': 15,
        'SOL/USDT': 10,
        'DEFAULT': 10
    }
}
```

### Analysis Configuration
```python
PHEMEX_ANALYSIS_CONFIG = {
    'volume_spike_threshold': 2.0,   # 2x average volume
    'min_volume_usdt': 100000,      # Minimum 24h volume
    'price_change_threshold': 0.02,  # 2% price change threshold
    'rsi_period': 14,               # RSI calculation period
    'rsi_overbought': 70,           # RSI overbought level
    'rsi_oversold': 30,             # RSI oversold level
}
```

## 🎯 Trading Strategies

### Signal Generation
The bot generates signals based on:

1. **RSI Analysis**: Oversold (<30) or Overbought (>70)
2. **EMA Crossover**: Short-term vs long-term trend
3. **Volume Spikes**: Unusual trading volume
4. **Price Momentum**: Recent price movements

### Risk Management
- **Stop Loss**: 2% automatic stop loss
- **Take Profit**: 3% and 6% take profit levels
- **Position Sizing**: Based on account balance and risk tolerance
- **Daily Loss Limit**: Automatic trading halt at 10% daily loss

## 📈 Integration with Existing Systems

### Scanner Integration
The Phemex bot can be integrated with your existing scanners:

```python
# Add Phemex to your scanner
from phemex_exchange import PhemexExchange

# Initialize Phemex in your scanner
phemex = PhemexExchange(paper_trading=False)

# Use in your scanning logic
ticker = await phemex.get_ticker('BTC/USDT')
ohlcv = await phemex.get_ohlcv('BTC/USDT', '15m', 100)
```

### Market Maker Detection Integration
```python
# Use with your existing MM detection
from src.mm_detector import MMDetector
from phemex_exchange import PhemexExchange

mm_detector = MMDetector()
phemex = PhemexExchange()

# Get data from Phemex for MM analysis
df = await phemex.get_ohlcv('BTC/USDT', '15m', 300)
mm_signal = mm_detector.detect_patterns(df)
```

## 🚨 Safety Features

### Paper Trading Mode
- **Default Mode**: Always starts in paper trading
- **Simulated Orders**: No real money at risk
- **Realistic Simulation**: Includes slippage and fees
- **Easy Switching**: Simple config change to go live

### Risk Controls
- **API Key Security**: Never log or expose API keys
- **Position Limits**: Maximum positions and size limits
- **Daily Loss Limits**: Automatic trading halt
- **Leverage Limits**: Symbol-specific leverage caps

## 📱 Monitoring & Alerts

### Discord Integration
- **Trade Alerts**: Real-time trade notifications
- **Error Alerts**: System error notifications
- **Performance Updates**: Daily performance summaries
- **Position Updates**: Position status changes

### Logging
- **Comprehensive Logs**: All activities logged
- **Performance Tracking**: Detailed trade statistics
- **Error Tracking**: Full error logs with stack traces
- **Audit Trail**: Complete trading history

## 🔄 Running the Bot

### Development Mode
```bash
# Paper trading with detailed logs
python phemex_trading_bot.py
```

### Production Mode
1. Set `paper_trading=False` in config
2. Set `test=False` in PHEMEX_CONFIG
3. Ensure API keys are configured
4. Start the bot:
```bash
python phemex_trading_bot.py
```

### Background Running
```bash
# Run in background with nohup
nohup python phemex_trading_bot.py > bot.log 2>&1 &

# Or use screen/tmux
screen -S phemex_bot
python phemex_trading_bot.py
# Ctrl+A, D to detach
```

## 🛠️ Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check API key and secret
   - Verify API permissions
   - Check network connectivity

2. **No Signals Generated**
   - Adjust analysis thresholds
   - Check market data quality
   - Verify symbol configurations

3. **Orders Not Executing**
   - Check account balance
   - Verify position limits
   - Check risk management settings

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 📊 Performance Optimization

### Recommended Settings
- **Scan Interval**: 60 seconds (adjust based on strategy)
- **Position Size**: Start small (1-2% of balance)
- **Leverage**: Conservative (5-10x for major pairs)
- **Risk Per Trade**: 2-5% maximum

### Monitoring
- **Daily P&L**: Monitor daily performance
- **Win Rate**: Track success rate
- **Drawdown**: Monitor maximum losses
- **Trade Frequency**: Adjust based on market conditions

## 🔐 Security Best Practices

1. **API Key Security**
   - Use read-only keys for testing
   - Enable IP restrictions
   - Rotate keys regularly
   - Never share API credentials

2. **Risk Management**
   - Start with small amounts
   - Use paper trading first
   - Set strict loss limits
   - Monitor positions regularly

3. **System Security**
   - Run on secure server
   - Use VPN if needed
   - Keep software updated
   - Backup configurations

## 📞 Support

For issues or questions:
1. Check the logs in `phemex_trading_bot.log`
2. Review the test output from `test_phemex_bot.py`
3. Verify your Phemex API settings
4. Check Phemex API documentation

## 🎉 Next Steps

1. **Test Thoroughly**: Run paper trading for at least a week
2. **Optimize Settings**: Adjust parameters based on results
3. **Monitor Performance**: Track metrics and adjust strategy
4. **Scale Gradually**: Start with small amounts and increase
5. **Stay Updated**: Keep the bot and dependencies updated

Happy Trading! 🚀


