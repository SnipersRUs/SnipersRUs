# Piv X Pro - Multi-Layer Reversal Detection System

## 🔔 Recent Updates (January 2026)

**Bug Fixes - Version 1.1:**
- ✅ **Fixed runtime errors on higher timeframes** - Resolved "bar index too far from current bar" errors that occurred when structure lines attempted to reference pivots from 500+ bars ago. Added proximity validation to ensure all drawing objects stay within Pine Script's limits.
- ✅ **Fixed VWAP calculation warnings** - Corrected conditional execution issues in Bottom/Top VWAP calculations where `ta.lowest()` and `ta.highest()` functions weren't executing on every bar, causing inconsistent results.
- ✅ **Improved multi-timeframe stability** - The indicator now runs smoothly across all timeframes (1m, 5m, 15m, 1H, 4H, Daily) without errors or warnings.

All core features and functionality remain unchanged. This update focused purely on stability improvements.

---

## Overview

Piv X Pro is an advanced technical analysis indicator that combines dynamic pivot detection, Williams %R momentum divergence analysis, and multiple VWAP anchoring methods to identify high-probability mean reversion opportunities. Unlike simple indicator combinations, this script implements a layered filtration system where each component validates and refines signals from the previous layer, resulting in significantly fewer but higher-quality reversal setups.

## Core Methodology

### 1. Dynamic ATR-Based Pivot Detection

The script uses an adaptive pivot detection algorithm that adjusts sensitivity based on market volatility. Instead of fixed lookback periods, pivot strength is calculated dynamically using Average True Range (ATR):

**Calculation:** `pivot_strength = max(min_strength, min(ATR / mintick * multiplier, max_strength))`

This ensures:
- More sensitive pivots in low volatility (smaller ATR)
- More significant pivots in high volatility (larger ATR)
- Automatic adaptation across different market conditions and timeframes

**Significance Filtering:** Pivots must exceed a minimum ATR distance from recent price action (default 0.3 ATR) to filter noise. This prevents minor price fluctuations from being marked as significant pivots.

**Volume Confirmation (Optional):** Pivots can optionally require volume spikes (default 1.5x average volume) to ensure institutional participation.

### 2. Williams %R Momentum Divergence Engine

The script detects classic and hidden divergences between price pivots and Williams %R oscillator readings:

**Bullish Divergence Detection:**
- Price makes a lower low (confirmed pivot low)
- Williams %R makes a higher low (momentum improving)
- Divergence occurs in oversold zone (Williams %R ≤ -80)
- Lookback range: 60 bars maximum

**Bearish Divergence Detection:**
- Price makes a higher high (confirmed pivot high)
- Williams %R makes a lower high (momentum weakening)
- Divergence occurs in overbought zone (Williams %R ≥ -20)
- Lookback range: 60 bars maximum

**Divergence-Anchored VWAPs:** When a divergence is detected, a new VWAP calculation begins from that point, tracking institutional positioning relative to the momentum shift. This provides a dynamic mean reversion target that resets at each confirmed divergence.

### 3. Confluence Scoring System

Each detected pivot receives a numerical score (0-150+ points) based on multiple independent confirmation factors:

**Scoring Components:**
- Base Pivot Detection: 10 points
- Volume Spike Confirmation: 15 points
- Higher Timeframe Trend Alignment (4H EMA): 20 points
- RSI Extreme Levels (oversold/overbought): 25 points
- Mean Reversion Distance (>2.5 ATR from HTF MA): 20 points
- Exhaustion Patterns (price move + volume spike): 10 points
- ATR Price Confirmation: 10 points
- RSI Divergence: 15 points
- Swing Failure Pattern (SFP): 15 points
- Liquidity Sweep: 10 points
- Candle Reversal Confirmation: 10 points
- Key Level Alignment (previous day/week highs/lows): 10 points
- Fair Value Gap (FVG) Fill: 10 points
- Session Weighting (London/NY sessions): 10 points
- Multi-Timeframe Pivot Confluence: 15 points

**Zone Classification:**
- Regular Zones: Score 60-89 (green/purple boxes)
- Golden Zones: Score 90+ (yellow boxes with thicker borders)

Higher scores indicate stronger confluence and higher probability setups, but no prediction is guaranteed.

### 4. Mean Reversion Distance Filter

The script calculates how far price has stretched from the higher timeframe moving average:

**Calculation:** `distance_from_htf_ma = (close - HTF_EMA) / ATR`

**Mean Reversion Condition:**
- For long setups: Price >2.5 ATR below HTF EMA when HTF trend is up
- For short setups: Price >2.5 ATR above HTF EMA when HTF trend is down

This ensures pivots are only highlighted when price is statistically stretched and likely to revert toward the mean.

### 5. Multi-Period VWAP Framework

The script provides multiple VWAP calculations for different analysis purposes:

**Extreme VWAPs:**
- Bottom VWAP: Anchored to the absolute lowest low in the lookback period (default 50 bars)
- Top VWAP: Anchored to the absolute highest high in the lookback period

**Periodic VWAPs:**
- 4D VWAP: Resets every 4 days
- 9D VWAP: Resets every 9 days
- 4H VWAP: Resets every 4 hours
- 8H VWAP: Resets every 8 hours
- Weekly VWAP: Resets at the start of each week
- Monthly VWAP: Resets at the start of each month
- Yearly VWAP: Resets at the start of each year

**Previous Period VWAPs:**
- Previous Weekly, Monthly, and Yearly VWAPs are displayed as reference levels for support/resistance

**Divergence VWAPs:**
- Bullish Divergence VWAP: Resets at each bullish Williams %R divergence
- Bearish Divergence VWAP: Resets at each bearish Williams %R divergence

### 6. IBSS Pro Mean Reversion System

An integrated scalping system that provides entry signals within high-probability pivot zones:

**Components:**
- Dual EMA System: Fast EMA (12) and Slow EMA (26) with color-coded trend visualization
- RSI Oversold/Overbought Detection: Configurable levels (default 30/70)
- Zone-Based Entry: Signals only trigger when price is within active pivot zones (0.3 ATR around confirmed pivots)
- ATR-Based Dynamic Stops: Stop losses trail with position using ATR multiplier

**Signal Generation:**
- Buy signals: RSI crosses above oversold + Fast EMA > Slow EMA + Price in pivot low zone
- Sell signals: RSI crosses below overbought + Fast EMA < Slow EMA + Price in pivot high zone

## Why This Combination is Unique

This is not a simple indicator mashup. The components work together in a specific hierarchy:

1. **Williams %R Divergence** identifies momentum shifts before price confirms the reversal
2. **Dynamic Pivots** mark actual price structure extremes with ATR-based significance filtering
3. **Confluence Scoring** quantifies setup quality using 10+ independent confirmation factors
4. **Mean Reversion Distance** confirms price is statistically stretched (>2.5 ATR from HTF MA)
5. **VWAP Framework** tracks institutional positioning and provides objective mean levels
6. **IBSS Signals** provide precise entries within high-probability zones

Each layer filters the previous one, resulting in significantly fewer but higher-quality signals than any single indicator alone. The divergence-anchored VWAPs are unique - they reset at momentum shifts rather than arbitrary time periods, providing more relevant mean reversion targets.

## How to Use This Indicator

### For Swing Trading (15m-1H Charts)

1. Wait for a major pivot to form (diamond marker appears below/above bars)
2. Check the confluence score displayed in the zone label
3. Look for Golden Zones (score 90+, yellow boxes with thicker borders)
4. Enter when price enters the pivot zone (0.3 ATR around the pivot)
5. Use the nearest VWAP level as first target
6. Set stop loss beyond the pivot zone (typically 0.5-1 ATR)

### For Scalping (5m-15m Charts)

1. Enable IBSS Pro Signals in settings
2. Wait for price to enter an active pivot zone (colored boxes appear)
3. Take IBSS diamond signals that form within zones
4. Use ATR-based stop losses (dashed lines appear automatically if enabled)
5. Exit at pivot VWAP or opposite zone edge

### Visual Elements Explained

- **White/Purple Crosses**: Williams Divergence VWAPs (momentum-based mean reversion targets)
- **Green/Red Crosses**: Bottom/Top VWAPs (absolute extreme levels)
- **Colored Boxes**: Pivot reversal zones (opacity indicates confluence score)
- **Yellow Boxes**: Golden zones (90+ score, highest probability setups)
- **Small Diamonds**: Regular pivot detections
- **Green/Red Tiny Diamonds**: IBSS scalp entry signals (if enabled)
- **White/Purple MAs**: IBSS trend filter (12/26 EMA with cloud)
- **Dotted Lines**: Structure lines connecting consecutive pivots of same type
- **Blue Dashed Lines**: Market Structure Shift (CHoCH) markers

### Recommended Settings

**Conservative (Lower Timeframes 1m-5m):**
- ATR Pivot Strength: 0.8-1.0
- Volume Threshold: 2.0
- Min Pivot Significance: 0.4-0.5
- Enable ATR Confirmation: Yes
- Real-Time Mode: Off
- Score Threshold: 80+

**Aggressive (Higher Timeframes 15m-1H):**
- ATR Pivot Strength: 0.6-0.8
- Volume Threshold: 1.5
- Min Pivot Significance: 0.3
- Enable ATR Confirmation: No
- Real-Time Mode: On
- Score Threshold: 60+

## Chart Requirements

This indicator should be used **alone on a clean chart** with:
- Standard candlestick or bar chart type (NO Heikin Ashi, Renko, Point & Figure, or Range charts)
- No other indicators overlaid (all functionality is self-contained)
- Symbol and timeframe clearly visible in chart
- Full indicator name "Piv X Pro" visible in chart legend

## Important Disclaimers

- Past performance does not guarantee future results
- All signals are probabilistic indicators, not trading guarantees
- Use proper risk management and position sizing
- Test thoroughly on demo accounts before live trading
- Higher confluence scores indicate better setups but no prediction is certain
- Mean reversion strategies work best in ranging/choppy markets; may underperform in strong trending markets
- The lookahead bias warning: HTF EMA uses `barmerge.lookahead_on` for trend filtering only (not for signal generation), which may cause historical bars to show different trend states than real-time

## Key Differentiators

Unlike basic pivot or VWAP indicators:
- **Dynamic ATR-based pivot detection** vs static lookback periods
- **Quantified confluence scoring** vs subjective interpretation
- **Mean reversion distance filtering** (>2.5 ATR from HTF MA) vs all pivots shown
- **Divergence-anchored VWAPs** vs static period VWAPs
- **Multi-layer confirmation system** (10+ independent factors) vs single signal generation
- **Integrated scalping system** that only triggers in high-probability zones

This script is open-source and available for educational purposes. Users are encouraged to understand the methodology before using it for live trading decisions.
