# Spot Buy Buoys Indicator

## Overview

The **Spot Buy Buoys Indicator** overlays spot buying activity on futures charts, helping you identify when there's significant spot buying pressure even as futures price moves down. This divergence can signal potential reversals or accumulation zones.

## Key Features

### 🎯 Spot Buy Detection
- **Volume Analysis**: Detects volume spikes that indicate absorption (spot buying)
- **Order Flow Pressure**: Analyzes price action to estimate buy vs sell pressure
- **Intensity Levels**: Classifies buying pressure as WEAK, MODERATE, or STRONG

### ⚡ Divergence Detection
- **Price Down + Spot Buy**: Highlights when price is dropping but spot buying is increasing
- **Visual Alerts**: Yellow diamond markers and background highlighting for divergence
- **Customizable Thresholds**: Adjust sensitivity for price drops and buy pressure

### 📊 Visual Elements
- **Buoys**: Circular markers below bars showing spot buy activity
- **Intensity Lines**: Colored lines connecting low to close showing buy pressure
- **Info Table**: Real-time display of buy pressure, intensity, price trend, and divergence status
- **Color Coding**:
  - Blue = Weak Buy
  - Aqua = Moderate Buy
  - Lime = Strong Buy
  - Yellow = Divergence (Price Down + Spot Buy)

## How It Works

Since Pine Script cannot directly fetch spot market data from exchanges, the indicator uses intelligent proxies:

1. **Volume-Based Detection**:
   - Compares current volume to average volume
   - Identifies volume spikes with minimal price movement (absorption)
   - Calculates buy pressure from price change and volume ratios

2. **Order Flow Analysis**:
   - Analyzes candlestick structure (body, wicks)
   - Large lower wicks = rejection of lows = buying support
   - Body size and direction indicate buying vs selling pressure

3. **Divergence Logic**:
   - Monitors price trend over lookback period
   - When price drops below threshold AND buy pressure is high = divergence
   - This suggests spot buyers are accumulating while futures sell off

## Installation

1. Open TradingView
2. Go to Pine Editor
3. Copy the contents of `spot_buy_buoys_indicator.pine`
4. Paste into Pine Editor
5. Click "Add to Chart"
6. Apply to any futures chart (BTCUSDT, ETHUSDT, etc.)

## Settings Guide

### Spot Buy Detection
- **Volume Lookback** (20): Number of bars to calculate average volume
- **Volume Spike Threshold** (1.5x): How much above average volume triggers detection
- **Buy Pressure Period** (14): Period for smoothing buy pressure calculations
- **Min Buy Pressure %** (60%): Minimum buy pressure to show a buoy

### Divergence Detection
- **Divergence Lookback** (10): Bars to check for price trend
- **Price Drop Threshold** (-0.5%): How much price must drop to trigger divergence
- **Min Divergence Strength** (70%): Minimum buy pressure during divergence

### Display Settings
- **Show Spot Buy Buoys**: Toggle buoy markers on/off
- **Show Intensity Levels**: Toggle colored lines showing intensity
- **Show Divergence**: Toggle divergence highlighting
- **Buoy Size**: Adjust marker size (Tiny/Small/Normal/Large)
- **Show Text Labels**: Toggle text on buoys

## Trading Ideas

### Bullish Divergence Setup
When you see:
- ⚡ Yellow diamond buoys (divergence detected)
- Price dropping but buy pressure > 70%
- Volume increasing

**Potential Action**:
- Watch for reversal signals
- Consider long entries if price holds support
- Stop loss below recent low

### Strong Spot Buying
When you see:
- 🟢 Lime (STRONG) buoys appearing
- Consistent buy pressure > 80%
- Price stabilizing or rising

**Potential Action**:
- Spot buyers are active
- May indicate accumulation
- Monitor for breakout above resistance

### Weak Spot Buying
When you see:
- 🔵 Blue (WEAK) buoys
- Buy pressure 50-65%

**Potential Action**:
- Less significant signal
- Wait for stronger confirmation
- May indicate minor support

## Limitations

⚠️ **Important**: This indicator uses proxies based on futures chart data, not actual spot market data. For the most accurate spot buying signals, you would need:
- Real-time spot market data feed
- Order book analysis
- Trade-by-trade data

The proxies used here are designed to approximate spot buying activity through volume and price action analysis, which often correlates with actual spot market behavior.

## Advanced Usage

### Customizing for Different Timeframes
- **Scalping (1m-5m)**: Lower volume threshold (1.2x), shorter lookback (10)
- **Swing Trading (1h-4h)**: Higher threshold (2.0x), longer lookback (30)
- **Position Trading (Daily)**: Very high threshold (2.5x), lookback (50)

### Combining with Other Indicators
- Use with VWAP for confluence
- Combine with support/resistance levels
- Add volume profile for context
- Use with funding rate indicators

## Troubleshooting

**No buoys showing?**
- Lower the "Min Buy Pressure %" setting
- Check that "Show Spot Buy Buoys" is enabled
- Ensure sufficient volume on the chart

**Too many buoys?**
- Increase "Min Buy Pressure %" threshold
- Increase "Volume Spike Threshold"
- Adjust "Volume Lookback" period

**Divergence not triggering?**
- Lower "Price Drop Threshold" (more negative)
- Lower "Min Divergence Strength"
- Increase "Divergence Lookback" period

## Future Enhancements

Potential improvements (would require external data feed):
- Real spot market data integration
- Order book imbalance analysis
- Trade-by-trade flow analysis
- Multi-exchange spot data aggregation

## Support

For questions or issues, refer to the main project documentation or create an issue in the repository.

---

**Disclaimer**: This indicator is for educational purposes only. It does not provide financial advice. Always do your own research and risk management.

