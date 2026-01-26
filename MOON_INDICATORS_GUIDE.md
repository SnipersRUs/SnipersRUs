# Moon Phase Indicators Guide

## 🆕 New Features Added

### 1. **Moon Phase Moving Average** (Off by Default)
### 2. **Moon Cycle VWAP** (Off by Default)

Both are located in the **"Moon Indicators"** settings group.

---

## 📊 Moon Phase Moving Average

### **How It Works:**
- **Adaptive Moving Average** that changes its period based on the current moon phase
- **More responsive during Waxing Moon** (bullish phase): Uses shorter period (50-75% of base)
- **Smoother during Waning Moon** (bearish phase): Uses longer period (75-100% of base)

### **Settings:**
- `Show Moon Phase MA` - Toggle on/off (default: OFF)
- `Base MA Period` - Base period for calculation (default: 20, range: 5-100)
- `Moon Phase MA` - Color customization (default: blue)

### **How to Use:**
1. **Enable** "Show Moon Phase MA"
2. **Adjust** "Base MA Period" to your preference (10-50 recommended)
3. **Watch** the MA adapt to moon phases:
   - **Waxing Phase**: MA becomes more responsive (faster)
   - **Waning Phase**: MA becomes smoother (slower)

### **Trading Applications:**
- **Price Above MA during Waxing** = Strong bullish signal
- **Price Below MA during Waning** = Bearish confirmation
- **MA Crosses** during phase transitions = Potential reversal signals

---

## 📈 Moon Cycle VWAP

### **How It Works:**
- **Volume Weighted Average Price** that **resets at each New Moon**
- Calculates VWAP from the start of the current moon cycle (~29.5 days)
- Resets automatically when a new moon is detected

### **Settings:**
- `Show Moon Cycle VWAP` - Toggle on/off (default: OFF)
- `Moon Cycle VWAP` - Color customization (default: purple)

### **How to Use:**
1. **Enable** "Show Moon Cycle VWAP"
2. **Watch** the VWAP reset at each new moon (🌑)
3. **Use** as support/resistance for the current moon cycle

### **Trading Applications:**
- **Price Above VWAP** = Bullish momentum for current cycle
- **Price Below VWAP** = Bearish momentum for current cycle
- **VWAP as Support/Resistance** = Key levels during moon cycle
- **VWAP Resets** = New cycle = New reference point

### **Key Features:**
- ✅ Automatically resets at New Moon
- ✅ Accounts for volume-weighted price
- ✅ Provides cycle-specific reference level
- ✅ Works on all timeframes (best on daily/weekly)

---

## 🎯 Combined Strategy

### **Bullish Setup:**
1. **Waxing Moon Phase** (▲ green indicator)
2. **Price > Moon Phase MA** (faster MA confirms trend)
3. **Price > Moon Cycle VWAP** (above cycle average)
4. **Green Background** (bullish phase confirmed)

### **Bearish Setup:**
1. **Waning Moon Phase** (▼ red indicator)
2. **Price < Moon Phase MA** (slower MA confirms trend)
3. **Price < Moon Cycle VWAP** (below cycle average)
4. **Red Background** (bearish phase confirmed)

### **Reversal Signals:**
- **New Moon Reset** = VWAP resets, new cycle begins
- **MA Period Change** = Phase transition affects responsiveness
- **Full Moon** = Peak of cycle, potential reversal zone

---

## ⚙️ Recommended Settings

### **For Swing Trading (Daily Charts):**
- Moon Phase MA: Base Period = 20-30
- Moon Cycle VWAP: Enable both
- Best for: Medium-term positions

### **For Day Trading (Intraday Charts):**
- Moon Phase MA: Base Period = 10-15
- Moon Cycle VWAP: Less effective (needs daily candles for cycle)
- Best for: Quick entries/exits

### **For Position Trading (Weekly Charts):**
- Moon Phase MA: Base Period = 10-20
- Moon Cycle VWAP: Excellent for long-term cycles
- Best for: Multi-cycle positions

---

## 📊 Technical Details

### **Moon Phase MA Calculation:**
```
Phase Weight = 1.0 at New Moon → 0.0 at Full Moon → 1.0 at next New Moon
Adaptive Period = Base Period × (1.0 - Phase Weight × 0.5)
Result: 50% to 100% of base period
```

### **Moon Cycle VWAP Calculation:**
```
VWAP = Sum(Price × Volume) / Sum(Volume)
Reset at: New Moon (phase < 0.03 or phase > 0.97)
Cycle Length: ~29.5 days (varies)
```

---

## 💡 Pro Tips

1. **Start with VWAP** - It's simpler and more reliable
2. **Combine with Bear/Bull Indicators** - Use ▲/▼ signals for confirmation
3. **Watch for Resets** - New moon = fresh VWAP = new trading opportunities
4. **Timeframe Matters** - Daily charts work best for moon cycle analysis
5. **Don't Over-Optimize** - Keep base MA period reasonable (10-50)

---

## ⚠️ Important Notes

- **Moon indicators are off by default** - Enable them as needed
- **VWAP needs volume data** - Works best on exchanges with volume
- **MA adapts smoothly** - Changes aren't sudden, but gradual
- **Combine with other analysis** - Don't rely solely on moon indicators
- **Risk management always** - Use stops regardless of moon phase

---

## 🎨 Visual Guide

When enabled, you'll see:
- **Blue Line** = Moon Phase MA (adaptive)
- **Purple Line** = Moon Cycle VWAP (resets at new moon)
- **Background Colors** = Green (bullish) / Red (bearish)
- **Triangle Indicators** = ▲ (bull) / ▼ (bear)

Both indicators complement the existing moon phase markers and bear/bull signals!
