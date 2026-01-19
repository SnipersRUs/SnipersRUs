# Piv X Pro - Changelog

## Version 1.1 - January 2026

### 🐛 Bug Fixes

**Fixed Runtime Errors on Multiple Timeframes**
- **Fixed: Bar index out of range error** - Structure lines (dotted lines connecting pivots) were attempting to reference bar indices from thousands of bars ago, exceeding Pine Script's 500-bar limit. Added proximity validation to only draw structure lines when previous pivots are within valid range.

- **Fixed: Conditional execution warnings** - `ta.lowest()` and `ta.highest()` functions in Bottom/Top VWAP calculations were being called conditionally, causing inconsistent results. Refactored to ensure these functions execute on every bar as required by Pine Script.

- **Improved stability across all timeframes** - The indicator now works reliably on 1m, 5m, 15m, 1H, 4H, and Daily charts without runtime errors.

### 📝 Technical Details

**Structure Line Drawing (Lines 584-608)**
- Added `max_line_bars = 500` constant
- Implemented bar distance validation before drawing
- Prevents "bar index too far from current bar" errors

**VWAP Calculations (Lines 271-303)**
- Extracted `ta.lowest()` and `ta.highest()` to unconditional variables
- Ensures series functions maintain proper state on every bar
- Eliminates "might not execute on every bar" warnings

---

## Version 1.0 - January 2026

### 🎉 Initial Release

**Core Features:**
- Dynamic ATR-based pivot detection with adaptive sensitivity
- Williams %R momentum divergence analysis with divergence-anchored VWAPs
- Multi-layer confluence scoring system (0-150+ points)
- Mean reversion distance filtering (>2.5 ATR from HTF MA)
- Complete VWAP suite (Bottom/Top, 4D, 9D, 4H, 8H, Weekly, Monthly, Yearly)
- IBSS Pro integrated scalping system with zone-based entries
- Market structure analysis (CHoCH detection)
- Comprehensive alert system for all signal types

---

## Quick Update Note for TradingView

### Update - January 2026

**Bug Fixes:**
- ✅ Fixed runtime errors on higher timeframes (bar index out of range)
- ✅ Fixed conditional execution warnings in VWAP calculations
- ✅ Improved stability across all timeframes (1m to Daily)

The indicator now runs smoothly on all timeframes without errors. All core functionality remains unchanged.
