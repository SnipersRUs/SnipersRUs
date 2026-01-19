# Liquidation Reversal Hunter V2 - TradingView Description

## PUBLISHING CHECKLIST (Read Before Publishing!)

Before you publish, make sure you:

- [ ] **Use a STANDARD chart type** (Candlestick or Bar) - NOT Heikin Ashi, Renko, Kagi, etc.
- [ ] **Clean chart** - Remove ALL other indicators except this one
- [ ] **Show symbol and timeframe** clearly visible on chart
- [ ] **No drawings** unless explained in description
- [ ] **No external links** in description (no Discord, Telegram, websites)
- [ ] **No promotional language** ("Best indicator", "Join us", etc.)
- [ ] **Choose a good chart example** showing the indicator working clearly
- [ ] **Make it OPEN SOURCE** if you want to avoid the "closed-source originality" issues

**Why you keep getting banned:**
1. Your descriptions are too short - they need DETAIL about HOW it works
2. You're probably using Heikin Ashi charts - use CANDLESTICK only
3. You may have other indicators on the chart - remove them all
4. You may be combining indicators without explaining WHY they work together

---

**Copy the text below for your TradingView publication:**

---

## Liquidation Reversal Hunter V2

### What This Indicator Does

Liquidation Reversal Hunter V2 identifies potential reversal zones where significant liquidation events have occurred. It detects abnormal volume spikes combined with large price wicks—conditions that often precede price reversals when leveraged positions are forcibly closed.

The indicator displays:
- **Horizontal zone lines** marking where major liquidations likely occurred
- **Buy/Sell signals** when price action suggests a reversal from these zones
- **Heatmap coloring** showing the relative importance of each zone

---

### How It Works: The Methodology

#### 1. Volume Anomaly Detection (Z-Score Analysis)

The indicator uses statistical z-score analysis to identify abnormal volume:

```
Z-Score = (Current Volume - Average Volume) / Standard Deviation
```

- A z-score ≥ 2.0 indicates volume is 2 standard deviations above average (occurs ~2.5% of the time)
- Higher z-scores indicate increasingly rare and significant volume events
- The lookback period (default 50 bars) establishes the baseline for comparison

This statistical approach adapts to each asset's typical volume profile rather than using fixed thresholds.

#### 2. Liquidation Size Estimation

Liquidation magnitude is estimated by combining volume with price range:

```
Liquidation Size = (Volume in Millions) × (High - Low)
```

This proxy metric captures the "energy" of the move—large volume combined with large price movement suggests significant position liquidation. The indicator then calculates a z-score for this metric to identify statistically significant events.

#### 3. Stop Hunt Pattern Detection

The indicator identifies "stop hunt" patterns—where price sweeps beyond recent swing highs/lows then reverses:

**Bullish Stop Hunt:**
- Price makes a new 5 or 10-bar low
- Candle closes bullish (above open)
- Close is in the upper portion of the range
- Lower wick exceeds body size (for strong patterns)

**Bearish Stop Hunt:**
- Price makes a new 5 or 10-bar high
- Candle closes bearish (below open)
- Close is in the lower portion of the range
- Upper wick exceeds body size (for strong patterns)

These patterns often indicate that stops were triggered before price reversed.

#### 4. Multi-Factor Signal Strength Scoring

Each potential signal is scored on a 0-10 scale based on:

| Factor | Points | Logic |
|--------|--------|-------|
| Volume Z-Score | 0-2 | Higher abnormality = more points |
| Liquidation Magnitude | 0-2 | Larger events = more points |
| Stop Hunt Pattern | 0-2.5 | Strong patterns get bonus points |
| RSI Momentum | 0-1 | Oversold/overbought confirmation |
| Wick Rejection | 0-1.5 | Larger wicks indicate stronger rejection |
| Divergence (optional) | 0-1 | RSI/MACD divergence confirmation |

Signals only trigger when the combined score meets the minimum threshold (default: 2).

#### 5. Smart Zone Cleanup System

Unlike static level indicators, zones are dynamically managed:

- **Tagging**: When price touches a zone, it's marked as "tagged"
- **Sweep Removal**: When price closes beyond a zone, it's removed (level has been "taken out")
- **Time Decay**: Zone importance decays over time (default: 1% per bar)
- **Age Limits**: Old zones are removed unless they maintain high importance

This prevents chart clutter from stale levels.

---

### Why These Components Work Together

The indicator combines three distinct edge concepts:

1. **Volume Anomalies** identify when unusual activity is occurring—often institutional or liquidation-related
2. **Stop Hunt Patterns** identify the specific price action signature of liquidity grabs
3. **Statistical Thresholds** ensure only significant events are flagged, reducing false signals

The combination is more effective than any single approach:
- Volume alone would flag many non-reversal events
- Wicks alone would miss the volume context
- Stop hunts alone might catch minor moves

Together, they filter for high-probability reversal setups where:
- Significant volume entered the market
- Price made an extreme move (likely triggering stops)
- Price action rejected the extreme (wick formation)

---

### How to Use This Indicator

**For Entries:**
1. Wait for a signal flag to appear
2. Confirm with your own analysis (trend, structure, etc.)
3. Consider the zone line as a potential support/resistance level

**For Zone Analysis:**
- **Brighter/thicker lines** = higher importance zones
- **Green zones** = short liquidations occurred (potential support)
- **Red zones** = long liquidations occurred (potential resistance)
- **Dashed lines** = zones that have been tested (tagged)

**Recommended Settings:**
- Lower timeframes (1m-15m): Use stricter filters, fewer max lines
- Higher timeframes (1H+): Can use default or relaxed settings
- High volatility: Increase z-score threshold
- Low volatility: Decrease thresholds

**Best Practices:**
- Use with trend analysis—reversals are higher probability with trend
- Don't trade every signal—use as confluence with other analysis
- Monitor zone reactions—price behavior at zones provides information

---

### Input Settings Explained

**Liquidation Detection:**
- Volume Multiplier: How many times above average volume must be
- Z-Score Threshold: Statistical significance level (2.0 = 95th percentile)
- Min Liquidation Size: Minimum estimated liquidation in millions

**Signal Quality:**
- Stop Hunt Detection: Enable sweep-and-reversal pattern detection
- Divergence Filter: Require RSI/MACD divergence (reduces signals)
- Momentum Filter: Require RSI oversold/overbought
- Signal Cooldown: Minimum bars between signals

**Zone Cleanup:**
- Tagged Zone Lifespan: Bars before tested zones disappear
- Max Zone Age: Oldest zones allowed
- Age Decay Rate: How fast importance decreases

---

### Limitations and Disclaimers

- This indicator identifies potential reversal zones, not guaranteed reversals
- Volume data quality varies by exchange and asset
- Works best on liquid assets with reliable volume data
- Past liquidation zones do not guarantee future reactions
- Always use proper risk management and position sizing
- This is a tool for analysis, not a complete trading system

---

### Summary

Liquidation Reversal Hunter V2 uses statistical analysis of volume anomalies, price action patterns, and dynamic zone management to identify where significant liquidation events have likely occurred. The multi-factor scoring system filters for higher-probability setups while the smart cleanup system keeps the chart clean and focused on relevant levels.

---

**Tags:** liquidation, reversal, volume, stop-hunt, support-resistance, zones, statistical-analysis
