# Piv X Pro Update Announcement

## Short Version (Discord/Social Media)

```
🔧 **PIV X PRO - HOTFIX UPDATE** 🔧

Just pushed stability improvements to fix runtime errors reported on higher timeframes.

✅ Fixed: Bar index out of range errors
✅ Fixed: VWAP calculation warnings
✅ Improved: Multi-timeframe stability (1m-Daily)

All features work exactly the same - this is purely a stability update.

📊 **Get it:** https://www.tradingview.com/script/EzLLjhiA-Piv-X/

Working perfectly on all timeframes now! 🎯
```

## Detailed Version (TradingView Update Notes)

**Piv X Pro v1.1 - Stability Update**

Fixed critical runtime errors that were affecting performance on multiple timeframes:

1. **Bar Index Out of Range** - Structure lines (the dotted lines connecting pivots) were trying to reference bar indices too far back. Added validation to only draw when previous pivots are within 500 bars of current price.

2. **VWAP Calculation Warnings** - Bottom/Top VWAP functions were executing conditionally, causing "might not execute on every bar" warnings. Refactored to ensure proper series function execution.

3. **Multi-Timeframe Testing** - Verified stable operation on 1m, 5m, 15m, 1H, 4H, and Daily charts.

**No feature changes** - all signals, VWAPs, zones, and alerts work exactly as before. This update only improves underlying code stability.

## Technical Details (For Code Documentation)

**Changes in v1.1:**

**Structure Line Drawing (Lines 584-608)**
```pine
// Added proximity check before drawing
max_line_bars = 500
bars_back_pl = bar_index - prev_major_pl_bar
if bars_back_pl <= max_line_bars
    // Only draw if within valid range
```

**VWAP Calculations (Lines 271-303)**
```pine
// Extracted to unconditional variables
lowest_low_check = ta.lowest(low, extreme_vwap_lookback)  // Always executes
lowest_low_offset = ta.barssince(low == lowest_low_val and low == lowest_low_check)
```

**Impact:**
- Eliminates "bar index X is too far from current bar" errors
- Eliminates "might not be calculated on every bar" warnings
- Maintains all original functionality without behavior changes
