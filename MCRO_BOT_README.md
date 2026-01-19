# MCRO Bot - Enhanced SR+VWAP Scanner

## Overview
MCRO Bot is an advanced cryptocurrency trading scanner that focuses on **macro coins** (established cryptocurrencies) with enhanced risk management and safer trading strategies.

## Key Features
- **Macro Coin Focus**: Only trades established cryptocurrencies with proven track records
- **Multi-timeframe Analysis**: Combines 1h and 4h timeframes for better confluence
- **Enhanced SFP Detection**: Smart Money Concepts with volume validation
- **Dynamic Position Sizing**: Adjusts position size based on volatility and account performance
- **Risk Management**: Built-in invalidation levels and stop-loss management
- **Discord Integration**: Real-time notifications for all trading activities

## Trading Strategy
The bot scans for:
- **Support/Resistance + VWAP** confluence
- **Smart Money Concepts** (SFP - Stop Hunt Patterns)
- **Volume Profile** analysis
- **Fibonacci** retracement levels
- **Market Structure** (trending vs ranging)

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Discord Webhook
The Discord webhook is already configured in `config.py`:
```python
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1419912201124188161/u37vKgzcIff1nXnSk0NAaxlePMx6gRNYnlRHukdy6MmKDd3SZo_AZoAPtFqhclt8lJCB"
```

### 3. Test the Bot
```bash
python3 test_mcro_bot.py
```

### 4. Start the Bot
```bash
python3 run_mcro_bot.py
```

## Bot Behavior
- **Scanning**: Every hour, the bot scans all macro coins for high-confluence setups
- **Trading**: Takes up to 3 top opportunities per scan
- **Risk Management**: Maximum 5 open trades, dynamic position sizing
- **Notifications**: All trades and status updates sent to Discord

## Configuration
Key settings in `config.py`:
- `ACCOUNT_START`: Starting balance ($10,000)
- `POSITION_NOTIONAL`: Base position size ($1,000)
- `MAX_LEVERAGE`: Maximum leverage (10x)
- `MAX_OPEN_TRADES`: Maximum concurrent trades (5)

## Safety Features
- **Macro Coin Whitelist**: Only trades established cryptocurrencies
- **Volume Filters**: Minimum $5M daily volume requirement
- **Multi-Exchange Validation**: Must be available on at least 2 exchanges
- **Dynamic Risk Management**: Position sizing adjusts based on performance
- **Invalidation Levels**: Trades are closed if market structure breaks

## Discord Notifications
The bot sends notifications for:
- 🚀 Bot startup
- 🟢 New long trades
- 🔴 New short trades
- 📊 Status updates (every 6 hours)
- 🛑 Bot shutdown

## Files
- `mcro_bot.py`: Main bot implementation
- `run_mcro_bot.py`: Simple runner script
- `test_mcro_bot.py`: Test script for verification
- `config.py`: Configuration settings
- `MCRO_BOT_README.md`: This documentation

## Support
The bot is designed for safer trading with established cryptocurrencies and includes comprehensive risk management features.


















































