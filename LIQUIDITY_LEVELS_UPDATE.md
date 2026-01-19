# Liquidity Levels - TradingView Update

## 🔧 Recent Fixes & Improvements

### Memory & Performance Fixes
- **Fixed Array Size Limits** - Added strict limits to prevent "Array too large" errors
  - Source array processing limited to 1,000 most recent items
  - Filtered arrays limited to 500 items maximum
  - Sorting operations limited to 200 items
- **Optimized Array Management** - Removed persistent arrays that could accumulate across bars
- **Improved Cleanup Logic** - More efficient filtering and merging of nearby lines

### Signal Quality Improvements
- **Balanced Signal Settings** - Adjusted defaults for optimal signal frequency
  - Min Importance: 40% (major liquidations only)
  - Min Signal Strength: 2 (requires confirmation)
  - Signal Cooldown: 6 bars (prevents spam)
- **Smart Exception Rule** - Very abnormal volume events can trigger signals with lower importance threshold
- **Tiny Flags** - Signals displayed as smallest possible flags to reduce chart clutter

### Visual Enhancements
- **Heatmap Color System** - Lines color-coded by importance (Blue → Yellow → Orange → Red)
- **Auto-Cleanup** - Lines automatically disappear when price moves 0.5 ATR through the level
- **Line Thickness** - Scales with importance (thicker = more significant)
- **Merged Nearby Lines** - Combines lines within 0.5% to reduce visual clutter

### Cleanup Features (Lower Timeframes)
- **Auto-Cleanup for Lower TFs** - Automatically stricter filters on timeframes ≤15 minutes
- **Max Lines Display** - Default 10 lines (adjustable)
- **Min Importance Filter** - Default 30% (adjustable)
- **Nearby Line Merging** - Enabled by default to reduce clutter

### Technical Improvements
- **Bar Index Limits** - Lines only drawn from bars within 500 bar lookback (Pine Script limit)
- **Safe Array Operations** - All array operations include size checks and limits
- **Error Prevention** - Multiple safeguards prevent memory issues

---

## ⚙️ Default Settings

**Signal Quality:**
- Min Importance for Signal: 40%
- Min Signal Strength: 2
- Signal Cooldown: 6 bars
- Divergence: Enabled
- Reversal Required: Enabled

**Line Cleanup:**
- Min Importance to Show: 30%
- Max Lines to Show: 10
- Merge Nearby Lines: Enabled
- Auto-Cleanup for Lower TFs: Enabled

**Visual:**
- Use Heatmap Colors: Enabled
- Line Length: 50 bars
- Line Opacity: 80%
- Line Width: 2

---

## 🎯 What This Means

- **More Reliable** - No more array size errors or memory issues
- **Better Signals** - Focused on major liquidations with quality confirmation
- **Cleaner Charts** - Automatic cleanup and merging reduce visual clutter
- **Works on All TFs** - Auto-adjusts for lower timeframes
- **Performance Optimized** - Efficient processing with strict limits

---

## 💡 Usage Tips

**For More Signals:**
- Lower Min Importance to 30-35%
- Lower Min Signal Strength to 1

**For Fewer, Higher Quality Signals:**
- Raise Min Importance to 50-60%
- Raise Min Signal Strength to 3-4

**For Lower Timeframes:**
- Auto-cleanup is enabled by default
- Adjust Max Lines to 5-7 for very low TFs
- Increase Min Importance to 40-50% for cleaner charts

---

**Liquidity Levels - Now more stable, efficient, and focused on major liquidity events.**
