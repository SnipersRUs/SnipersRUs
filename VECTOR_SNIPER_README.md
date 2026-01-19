# Vector Sniper Pro Scanner

Advanced cryptocurrency market scanner using the Vector Sniper Pro indicator logic. Scans MEXC, Bybit, and Binance exchanges for high-probability trading opportunities.

## 🎯 Features

- **Multi-Exchange Scanning**: MEXC (primary), Bybit, and Binance
- **Vector Sniper Pro Logic**: Complete implementation of the TradingView indicator
- **Real-time Discord Notifications**: Instant alerts with TradingView links
- **Signal Classification**: Extreme, Vector, and Pre-signals
- **Risk Management**: Built-in confidence scoring and filtering
- **TradingView Integration**: Direct links to charts for analysis

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Scanner
```bash
python run_vector_scanner.py
```

### 3. Continuous Scanning
```bash
python vector_sniper_scanner.py
```

## 📊 Signal Types

### 🚀 Extreme Signals
- Highest confidence signals
- TR Z-score ≥ 2.16 (1.2 × 1.8)
- Vol Z-score ≥ 1.8
- Immediate attention required

### ⚡ Vector Signals  
- Standard vector signals
- TR Z-score ≥ 1.2
- Vol Z-score ≥ 1.0
- High probability setups

### 📘 Pre-Signals
- Early warning signals
- Score ≥ 4/7
- Watch for confirmation
- Lower risk entries

## 🔧 Configuration

### Vector Sniper Parameters
```python
VECTOR_PARAMS = {
    'atr_len': 14,           # ATR period
    'vol_len': 20,           # Volume period  
    'tr_z_thr': 1.2,         # Volatility Z-score threshold
    'vol_z_thr': 1.0,        # Volume Z-score threshold
    'ext_mult': 1.8,         # Extreme multiplier
    'min_body_pct': 55,      # Minimum body percentage
    'pre_min_score': 4,      # Minimum pre-signal score
    'use_vwap': True,        # Require VWAP alignment
    'use_ema': True,         # Require EMA alignment
}
```

### Scanner Settings
```python
SCANNER_CONFIG = {
    'scan_interval': 1800,   # 30 minutes
    'max_signals_per_type': {
        'EXTREME': 5,
        'VECTOR': 8, 
        'PRE': 10
    },
    'min_confidence': 50,
}
```

## 📈 Discord Notifications

The scanner sends rich Discord embeds with:

- **Signal Classification**: Color-coded by signal type
- **TradingView Links**: Direct links to charts
- **Exchange Information**: MEXC, Bybit, Binance
- **Confidence Scores**: Risk assessment
- **Price Information**: Current prices and targets
- **Scan Summary**: Total signals found

### Discord Webhook
Configure your Discord webhook in `vector_sniper_config.py`:
```python
DISCORD_WEBHOOK = "your_webhook_url_here"
```

## 🎯 Trading Strategy

### Primary Exchange: MEXC
- All trading should be done on MEXC
- MEXC provides the most reliable signals
- Lower fees and better execution

### Risk Management
- **Position Size**: Maximum $100 per trade
- **Risk Per Trade**: 2% of account
- **Stop Loss**: 2% below entry
- **Take Profit**: 4% above entry
- **Leverage**: 1x (spot trading)

### Signal Priority
1. **Extreme Signals**: Immediate action
2. **Vector Signals**: Standard entries
3. **Pre-Signals**: Watch and wait

## 📊 Indicator Logic

### Core Components
- **ATR Analysis**: Volatility measurement
- **Volume Analysis**: Volume spike detection
- **Z-Score Filtering**: Statistical significance
- **Structure Breaks**: Support/resistance breaks
- **Trap Detection**: False breakout identification

### Pre-Signal Scoring (0-7 points)
- Spring/Upthrust detection
- No supply/demand zones
- Volume imbalance
- Volume ratio > 1.2x
- Trend alignment (VWAP/EMA)
- Price action confirmation

### Vector Conditions
- **Bull Vector**: Close > Open + TR Z ≥ 1.2 + Vol Z ≥ 1.0
- **Bear Vector**: Close < Open + TR Z ≥ 1.2 + Vol Z ≥ 1.0
- **Body %**: ≥ 55% of total range
- **Delta Ratio**: > 0.2 (bull) or < -0.2 (bear)

## 🔍 Exchange Support

### MEXC (Primary)
- **Symbols**: USDT pairs
- **Rate Limit**: 1000ms
- **Trading**: Spot only
- **Priority**: Highest

### Bybit
- **Symbols**: USDT pairs  
- **Rate Limit**: 1000ms
- **Trading**: Spot only
- **Priority**: Secondary

### Binance
- **Symbols**: USDT pairs
- **Rate Limit**: 1000ms  
- **Trading**: Spot only
- **Priority**: Secondary

## 📱 TradingView Integration

All signals include direct TradingView links:
```
https://www.tradingview.com/chart/?symbol=MEXC:BTCUSDT
https://www.tradingview.com/chart/?symbol=BYBIT:ETHUSDT
https://www.tradingview.com/chart/?symbol=BINANCE:ADAUSDT
```

## ⚠️ Risk Warning

- **High Risk**: Cryptocurrency trading involves significant risk
- **Educational Only**: This scanner is for educational purposes
- **No Financial Advice**: Not a substitute for professional advice
- **Risk Management**: Always use proper risk management
- **Test First**: Test with small amounts before larger trades

## 🛠️ Troubleshooting

### Common Issues
1. **No Signals**: Check exchange connectivity
2. **Discord Errors**: Verify webhook URL
3. **Rate Limits**: Increase delays between requests
4. **Memory Issues**: Reduce symbol limits

### Logs
- **Scanner Logs**: `vector_sniper_scanner.log`
- **Exchange Errors**: Check individual exchange logs
- **Discord Errors**: Check webhook responses

## 📞 Support

For issues or questions:
1. Check the logs for error messages
2. Verify exchange connectivity
3. Test Discord webhook manually
4. Review configuration settings

## 🔄 Updates

The scanner runs continuously every 30 minutes:
- **Scan Duration**: ~2-5 minutes per exchange
- **Total Time**: ~10-15 minutes for all exchanges
- **Signal Processing**: Real-time analysis
- **Discord Alerts**: Immediate notifications

## 📈 Performance

### Expected Results
- **Extreme Signals**: 0-3 per scan
- **Vector Signals**: 2-8 per scan  
- **Pre-Signals**: 5-15 per scan
- **Total Signals**: 7-26 per scan

### Signal Quality
- **High Confidence**: 70-95%
- **Medium Confidence**: 50-70%
- **Low Confidence**: 30-50%

---

**Vector Sniper Pro Scanner** - Advanced cryptocurrency market analysis



















































