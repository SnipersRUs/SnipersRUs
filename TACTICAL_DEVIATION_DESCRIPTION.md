# Tactical Deviation - TradingView Indicator Description

## Overview
Tactical Deviation is a multi-timeframe VWAP deviation tool that highlights how far price is from fair value (VWAP) using standard deviation bands. It can optionally add filters (volume confirmation, pivot reversals, RSI) and confluence checks across daily, weekly, and monthly VWAPs. The goal is to provide context around statistically stretched price areas and mark potential mean-reversion or continuation zones based on configurable rules.

## What It Plots
- Daily/weekly/monthly VWAP lines (independent toggles).
- Deviation bands at ±1σ, ±2σ, ±3σ for each enabled VWAP.
- Optional shaded fill between ±2σ bands.
- Signal markers (triangles) when deviation and filters meet the chosen criteria.
- A compact info table showing current deviation levels by timeframe.

## How It Works
1. For each enabled timeframe (daily/weekly/monthly), the script calculates VWAP using cumulative price*volume and cumulative volume within that period.
2. Standard deviation is computed from the same volume-weighted data. Bands are VWAP ± (stdDev * multiplier).
3. Deviation level is measured by how far price is from VWAP in units of standard deviation.
4. A signal can trigger when price reaches the configured deviation level and optional filters are satisfied:
   - Volume confirmation: volume exceeds a moving average by a chosen multiplier or recent momentum.
   - Pivot reversal: pivot highs/lows are detected and used as a directional filter.
   - RSI filter: oversold/overbought thresholds can be required.
   - Confluence: signals can require agreement from multiple VWAP timeframes.
5. Optional dynamic multipliers scale deviation bands based on ATR% to adapt to volatility.

## How To Use
- Use the deviation bands to assess whether price is within its normal range (inside ±1σ) or stretched (outside ±2σ/±3σ).
- Signals are only visual cues based on your selected filters. Consider them as alerts to review price behavior at extreme deviations rather than standalone trade instructions.
- If you trade intraday, start with Daily VWAP + ±2σ bands and volume confirmation, then add Weekly/Monthly VWAP for higher-timeframe context.

## Inputs Summary
- VWAP Settings: toggle daily/weekly/monthly VWAPs.
- Deviation Bands: toggle ±1σ/±2σ/±3σ and adjust multipliers.
- Dynamic Multipliers: scale bands using ATR% to reflect volatility.
- Signals: minimum deviation level, volume confirmation, pivot reversal, RSI filter.
- Confluence: require multiple VWAPs to agree before signaling.
- Visual: line widths, fill opacity, info table.

## Originality and Combination Rationale
This script combines multi-timeframe VWAP deviation, volatility-adjusted band scaling, and configurable confirmation filters (volume, pivots, RSI) into one workflow. The intent of the combination is to provide a single, consistent framework for viewing deviation-based context and optional confirmation criteria without requiring multiple separate indicators.

## Notes and Limitations
- This indicator does not use non-standard chart types; publish and evaluate it on standard candles.
- Signals are based on price deviation and optional filters and do not imply performance outcomes.
- Keep charts clean and include only this script unless additional tools are required and explained.
