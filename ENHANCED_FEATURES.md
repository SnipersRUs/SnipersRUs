# 🔴 Enhanced COOKED REVERSAL Scanner Features

## ✅ **Implemented Features**

### 📊 **Paper Trading System**
- **Starting Balance**: $10,000
- **Trade Size**: $300 per trade
- **Max Open Trades**: 3 positions maximum
- **Automatic Management**: Opens/closes positions based on TP/SL
- **State Persistence**: Saves trading state to `trading_state.json`

### 🚨 **Entry Notifications**
- **Separate Notifications**: Each trade entry gets its own Discord message
- **Detailed Analysis**: RSI, price extension, volume ratio
- **Target Levels**: TP1 (-5%), TP2 (-10%), TP3 (-20%), SL (+5%)
- **TradingView Links**: Direct links to charts for analysis

### 🔗 **TradingView Integration**
- **Clickable Tickers**: All ticker symbols are hyperlinked
- **Proper Format**: Tickers formatted as "SAGA/USDT"
- **Direct Links**: Links go to TradingView charts for each exchange
- **Watchlist Links**: Even watchlist items have TradingView links

### ⏰ **Rate Limiting**
- **Max Signals**: 3 signals per hour maximum
- **Prevents Spam**: Avoids overwhelming Discord with too many signals
- **Quality Focus**: Only shows the best opportunities

### 📈 **Position Tracking**
- **Real-time PnL**: Updates position values with current prices
- **Automatic Closes**: Monitors TP/SL levels and closes positions
- **Trade History**: Logs all trades with timestamps and results
- **Performance Stats**: Win rate, total PnL, trade count

### 🎯 **Smart Filtering**
- **Volume Range**: $100K - $10M USD volume filter
- **Score Threshold**: Minimum 50 score for signals
- **Priority Ordering**: Signals sorted by highest score first
- **Watchlist**: Additional qualifying setups on watchlist

## 🚀 **How to Use**

### **Run Enhanced Scanner:**
```bash
python3 run_enhanced_scanner.py
```

### **Run Direct:**
```bash
python3 cooked_reversal.py --loop --exchanges binance bybit mexc
```

## 📱 **Discord Notifications**

### **Entry Notification Example:**
```
🚨 ENTRY TAKEN 🚨

Symbol: SAGA/USDT (TradingView link)
Exchange: BYBIT
Entry Price: $0.36400000
Trade Size: $300
Score: 75/100

📊 Analysis:
• RSI: 78.5
• Price Extension: 12.3%
• Volume Ratio: 0.65

🎯 Targets:
• TP1: $0.34580000 (-5%)
• TP2: $0.32760000 (-10%)
• TP3: $0.29120000 (-20%)
• SL: $0.38220000 (+5%)
```

### **Main Scanner Card:**
- Trading summary with balance and PnL
- Current signals with TradingView links
- Watchlist with clickable tickers
- Performance statistics

## 📊 **Trading State File**
The scanner automatically saves trading state to `trading_state.json`:
- Current balance
- Open positions
- Trade history
- Performance metrics

## 🎯 **Key Benefits**
1. **No Over-trading**: Max 3 positions, rate limited
2. **Quality Signals**: Only best opportunities
3. **Full Tracking**: Complete PnL and performance monitoring
4. **Easy Analysis**: Direct TradingView links for every ticker
5. **Separate Notifications**: Clear entry alerts vs. general updates




