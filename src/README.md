# Enhanced Market Maker Detection & Trading System

A comprehensive system for detecting market maker activities and executing trades based on MM patterns, with advanced risk management and detailed trading cards.

## Features

### 🎯 Enhanced MM Pattern Detection
- **Iceberg Orders**: Detect large hidden orders through volume analysis
- **Spoofing**: Identify order book manipulation patterns
- **Layering**: Detect multiple orders at similar price levels
- **Major Flush Detection**: Alert on significant price movements that could signal reversals
- **Divergence Analysis**: Spot/futures pressure divergence detection
- **Bias Alignment**: Multi-timeframe bias analysis (M15, H1, H4)

### 💰 Advanced Trading System
- **Position Management**: Automated position sizing and risk management
- **Leverage Control**: Symbol-specific leverage limits (BTC: 20x, ETH/SOL: 10x)
- **Risk Management**: 10% max risk per trade, 15% max daily loss
- **Trading Cards**: Detailed entry/exit information for each trade
- **Performance Tracking**: Comprehensive P&L and win rate tracking

### 📊 Comprehensive Monitoring
- **Real-time Alerts**: Discord webhook integration for alerts
- **Trading Cards**: Detailed setup information for each trade
- **Portfolio Tracking**: Real-time balance and P&L monitoring
- **State Persistence**: Automatic state saving and recovery

## Installation

1. Install required dependencies:
```bash
pip install numpy pandas asyncio ccxt
```

2. Configure your settings in `mm_config.py`:
```python
# Update thresholds for your trading style
config.thresholds.divergence_threshold = 15.0
config.thresholds.mm_confidence_threshold = 35.0

# Set your Discord webhook
config.alerts.discord_webhook = "YOUR_DISCORD_WEBHOOK_URL"
```

## Usage

### Basic Usage
```python
from mm_trading_bot import MMTradingBot
import asyncio

async def main():
    bot = MMTradingBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Configuration
```python
from mm_config import config

# Adjust MM detection sensitivity
config.thresholds.divergence_threshold = 12.0  # More sensitive
config.thresholds.mm_confidence_threshold = 30.0  # Earlier detection

# Modify trading parameters
config.trading.position_size = 1500.0  # $1500 per trade
config.trading.max_risk_per_trade = 0.08  # 8% max risk

# Update leverage limits
config.trading.leverage_limits['BTC'] = 25
config.trading.leverage_limits['ETH'] = 15
```

## Market Maker Patterns Explained

### 1. Iceberg Orders
- **Detection**: High volume with low price volatility
- **Signal**: Large hidden orders being executed
- **Trading**: Look for accumulation/distribution patterns

### 2. Spoofing
- **Detection**: Large orders that disappear quickly
- **Signal**: Fake order book pressure
- **Trading**: Trade against the spoofing direction

### 3. Layering
- **Detection**: Multiple orders at similar price levels
- **Signal**: Systematic order placement
- **Trading**: Break through layered levels

### 4. Major Flush Detection
- **Detection**: 3%+ price move with 2x+ volume spike
- **Signal**: Potential reversal opportunity
- **Trading**: Wait for confirmation before entering

## Trading System Details

### Position Sizing
- **Base Size**: $1000 per trade
- **Risk Management**: 10% max risk per trade
- **Leverage**: BTC (20x), ETH/SOL (10x), Others (10x)
- **Max Positions**: 5 concurrent positions

### Entry Conditions
1. **MM Activity**: Active market maker with 35%+ confidence
2. **Bias Alignment**: H1/H4 bias alignment OR M15 with MM confirmation
3. **Risk/Reward**: Minimum 1.2:1 risk/reward ratio
4. **Pattern Confirmation**: At least one MM pattern detected

### Exit Conditions
- **Stop Loss**: 2x ATR below/above entry
- **Take Profits**: 1.5%, 3%, 5% targets
- **Risk Management**: 15% max daily loss

## Configuration Options

### MM Detection Thresholds
```python
# Divergence detection
divergence_threshold: float = 15.0  # Spot/futures pressure difference

# MM confidence
mm_confidence_threshold: float = 35.0  # Minimum confidence for MM activity

# Pattern detection
iceberg_threshold: float = 0.8  # Volume spike threshold
spoofing_threshold: float = 0.6  # Order book manipulation
layering_threshold: float = 0.7  # Layered orders
flush_threshold: float = 0.85  # Major flush detection
```

### Trading Parameters
```python
# Account settings
initial_balance: float = 10000.0
position_size: float = 1000.0
max_risk_per_trade: float = 0.10
max_daily_loss: float = 0.15
max_open_positions: int = 5

# Leverage limits
leverage_limits = {
    'BTC': 20,
    'ETH': 10,
    'SOL': 10,
    'DEFAULT': 10
}
```

## Alert Types

### 1. Trade Execution Alerts
- New position opened
- Position closed (stop loss/take profit)
- Risk management alerts

### 2. MM Pattern Alerts
- Iceberg order detection
- Spoofing pattern detected
- Layering pattern detected
- Major flush alerts

### 3. System Alerts
- Configuration issues
- Connection problems
- Performance metrics

## Performance Monitoring

### Key Metrics
- **Win Rate**: Percentage of profitable trades
- **Average P&L**: Average profit/loss per trade
- **Max Drawdown**: Maximum account drawdown
- **Sharpe Ratio**: Risk-adjusted returns
- **Total Trades**: Number of trades executed

### Trading Cards
Each trade includes detailed information:
- Entry/exit prices and timing
- Stop loss and take profit levels
- Position size and leverage
- MM pattern analysis
- Setup reason and confidence

## Risk Management

### Position Level
- Maximum 10% risk per trade
- Stop loss at 2x ATR
- Take profits at 1.5%, 3%, 5%

### Portfolio Level
- Maximum 5 open positions
- 15% maximum daily loss
- Symbol-specific leverage limits

### System Level
- State persistence and recovery
- Error handling and logging
- Configuration validation

## Troubleshooting

### Common Issues
1. **No trades executing**: Check MM confidence threshold and bias alignment
2. **Too many false signals**: Increase divergence threshold and MM confidence
3. **Missing patterns**: Verify data quality and pattern thresholds
4. **High drawdown**: Reduce position size or increase stop loss distance

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Always do your own research and consider your risk tolerance before trading.

