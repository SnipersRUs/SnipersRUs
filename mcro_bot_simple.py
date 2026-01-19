#!/usr/bin/env python3
"""
MCRO Bot — Simple 3 Signals Per Hour Scanner
"""

import os, json, time, math, traceback, requests, pytz
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import ccxt
import numpy as np
import pandas as pd
import config

# ========================= Core Configuration =========================
TZ_NY = pytz.timezone("America/New_York")
DATA_DIR = "data"
TRADES_JSON = os.path.join(DATA_DIR, "trades.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Alignment controls ----
# We run every 2 hours, aligned to minute = ALIGN_MINUTE and such that
# (hour - ANCHOR_HOUR_ET) % 2 == 0. Default anchors to 08:30 ET.
ALIGN_MINUTE      = 30     # run at :30
ANCHOR_HOUR_ET    = 8      # 08:30, 10:30, 12:30 ... ET
SCAN_INTERVAL_SEC = 7200   # 2 hours

# Top Macro Coins
TOP_MACRO_COINS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT', 'LINK/USDT',
    'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT', 'XLM/USDT',
    'NEAR/USDT', 'ICP/USDT', 'FIL/USDT', 'APT/USDT', 'ARB/USDT',
    'OP/USDT', 'INJ/USDT', 'TIA/USDT', 'SEI/USDT', 'SUI/USDT',
]

def now_str():
    return datetime.now(TZ_NY).strftime("%Y-%m-%d %H:%M:%S %Z")

def post_discord(content: str, embed=None):
    """Post to Discord webhook"""
    if not config.DISCORD_WEBHOOK:
        return
    try:
        payload = {"content": content} if content else {}
        if embed:
            payload["embeds"] = [embed]
        requests.post(config.DISCORD_WEBHOOK, json=payload)
    except:
        pass

def get_tradingview_link(symbol):
    """Generate TradingView link for MEXC ticker"""
    mexc_symbol = symbol.replace("/", "")
    return f"https://www.tradingview.com/chart/?symbol=MEXC:{mexc_symbol}"

def rsi(series: np.ndarray, length: int = 14) -> float:
    """Calculate RSI"""
    if len(series) < length + 1:
        return 50.0

    delta = np.diff(series)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-length:])
    avg_loss = np.mean(loss[-length:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ========================= GPS (Golden Pocket Syndicate) Logic =========================

def calculate_wave_trend(high, low, close, n1=10, n2=21):
    """Calculate Wave Trend oscillator"""
    ap = (high + low) / 2
    esa = pd.Series(ap).ewm(span=n1, adjust=False).mean()
    d = pd.Series(abs(ap - esa)).ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d + 1e-10)
    wt1 = pd.Series(ci).ewm(span=n2, adjust=False).mean()
    wt2 = pd.Series(wt1).rolling(4).mean()
    return wt1.values, wt2.values

def calculate_golden_pockets(df):
    """
    Calculate Golden Pockets for Daily, Weekly, Monthly (current and previous periods)
    GP = High - (High - Low) * 0.618 to 0.65
    """
    gp_data = {}

    # Daily GP (use last 24 hours of data as proxy)
    daily_high = df['high'].tail(24).max()
    daily_low = df['low'].tail(24).min()
    gp_data['daily_gp_high'] = daily_high - (daily_high - daily_low) * 0.618
    gp_data['daily_gp_low'] = daily_high - (daily_high - daily_low) * 0.65

    # Previous day GP
    if len(df) >= 48:
        prev_daily_high = df['high'].iloc[-48:-24].max()
        prev_daily_low = df['low'].iloc[-48:-24].min()
        gp_data['prev_daily_gp_high'] = prev_daily_high - (prev_daily_high - prev_daily_low) * 0.618
        gp_data['prev_daily_gp_low'] = prev_daily_high - (prev_daily_high - prev_daily_low) * 0.65
    else:
        gp_data['prev_daily_gp_high'] = gp_data['daily_gp_high']
        gp_data['prev_daily_gp_low'] = gp_data['daily_gp_low']

    # Weekly GP (use last 168 hours = 7 days)
    weekly_high = df['high'].tail(168).max()
    weekly_low = df['low'].tail(168).min()
    gp_data['weekly_gp_high'] = weekly_high - (weekly_high - weekly_low) * 0.618
    gp_data['weekly_gp_low'] = weekly_high - (weekly_high - weekly_low) * 0.65

    # Previous week GP
    if len(df) >= 336:
        prev_weekly_high = df['high'].iloc[-336:-168].max()
        prev_weekly_low = df['low'].iloc[-336:-168].min()
        gp_data['prev_weekly_gp_high'] = prev_weekly_high - (prev_weekly_high - prev_weekly_low) * 0.618
        gp_data['prev_weekly_gp_low'] = prev_weekly_high - (prev_weekly_high - prev_weekly_low) * 0.65
    else:
        gp_data['prev_weekly_gp_high'] = gp_data['weekly_gp_high']
        gp_data['prev_weekly_gp_low'] = gp_data['weekly_gp_low']

    # Monthly GP (use all available data as proxy)
    monthly_high = df['high'].max()
    monthly_low = df['low'].min()
    gp_data['monthly_gp_high'] = monthly_high - (monthly_high - monthly_low) * 0.618
    gp_data['monthly_gp_low'] = monthly_high - (monthly_high - monthly_low) * 0.65

    # Previous month GP (use first half if enough data)
    if len(df) >= 500:
        mid_point = len(df) // 2
        prev_monthly_high = df['high'].iloc[:mid_point].max()
        prev_monthly_low = df['low'].iloc[:mid_point].min()
        gp_data['prev_monthly_gp_high'] = prev_monthly_high - (prev_monthly_high - prev_monthly_low) * 0.618
        gp_data['prev_monthly_gp_low'] = prev_monthly_high - (prev_monthly_high - prev_monthly_low) * 0.65
    else:
        gp_data['prev_monthly_gp_high'] = gp_data['monthly_gp_high']
        gp_data['prev_monthly_gp_low'] = gp_data['monthly_gp_low']

    return gp_data

def is_near_gp(price, gp_low, gp_high, visibility_range_pct=2.0):
    """Check if price is near a Golden Pocket"""
    near_low = abs(price - gp_low) / price < (visibility_range_pct / 100)
    near_high = abs(price - gp_high) / price < (visibility_range_pct / 100)
    return near_low or near_high

def detect_order_blocks(df, gp_data, vol_avg, atr, ob_tighten_pct=5, ob_atr_mult=0.75, ob_vol_mult=1.20):
    """Detect bullish/bearish order blocks"""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_price = df['open'].values
    volume = df['volume'].values

    body = abs(close - open_price)
    body_pct = body / (high - low + 1e-10)
    range_atr = high - low

    current_price = close[-1]

    # Check if near GP
    near_bull_gp = (is_near_gp(current_price, gp_data['daily_gp_low'], gp_data['daily_gp_high']) or
                   is_near_gp(current_price, gp_data['weekly_gp_low'], gp_data['weekly_gp_high']) or
                   is_near_gp(current_price, gp_data['monthly_gp_low'], gp_data['monthly_gp_high']))

    # Bullish OB: strong bearish candle before reversal
    tight = 1.0 + ob_tighten_pct / 100.0
    bullish_ob = (
        close[-1] < open_price[-1] and  # Bearish candle
        body[-1] >= atr * ob_atr_mult * tight and
        range_atr[-1] >= atr * 1.0 and
        body_pct[-1] >= 0.42 and
        volume[-1] > vol_avg * ob_vol_mult and
        near_bull_gp
    )

    # Bearish OB: strong bullish candle before reversal
    bearish_ob = (
        close[-1] > open_price[-1] and  # Bullish candle
        body[-1] >= atr * ob_atr_mult * tight and
        range_atr[-1] >= atr * 1.0 and
        body_pct[-1] >= 0.42 and
        volume[-1] > vol_avg * ob_vol_mult and
        near_bull_gp
    )

    return bullish_ob, bearish_ob

def detect_sweeps(df, gp_data, vol_avg, atr, lookback=36, wick_min_pct=0.65, vol_mult=1.35):
    """Detect high-quality liquidity sweeps"""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_price = df['open'].values
    volume = df['volume'].values

    if len(df) < lookback + 1:
        return False, False

    # Previous extremes
    prev_low = np.min(low[-lookback-1:-1])
    prev_high = np.max(high[-lookback-1:-1])

    # Current candle metrics
    range_candle = high[-1] - low[-1]
    wick_lower = min(open_price[-1], close[-1]) - low[-1]
    wick_upper = high[-1] - max(open_price[-1], close[-1])
    body = abs(close[-1] - open_price[-1])

    wick_lower_pct = wick_lower / (range_candle + 1e-10)
    wick_upper_pct = wick_upper / (range_candle + 1e-10)
    body_pct = body / (range_candle + 1e-10)

    current_price = close[-1]
    near_strict_bull_gp = (
        abs(current_price - gp_data['daily_gp_low']) / current_price < 0.01 or
        abs(current_price - gp_data['weekly_gp_low']) / current_price < 0.01 or
        abs(current_price - gp_data['monthly_gp_low']) / current_price < 0.01
    )

    near_strict_bear_gp = (
        abs(current_price - gp_data['daily_gp_high']) / current_price < 0.01 or
        abs(current_price - gp_data['weekly_gp_high']) / current_price < 0.01 or
        abs(current_price - gp_data['monthly_gp_high']) / current_price < 0.01
    )

    # Sweep low (bullish): price sweeps below prev low, recovers above, big lower wick
    sweep_low = (
        low[-1] < prev_low and
        close[-1] > prev_low and
        wick_lower_pct >= wick_min_pct and
        body_pct <= 0.30 and
        volume[-1] > vol_avg * vol_mult and
        near_strict_bull_gp
    )

    # Sweep high (bearish): price sweeps above prev high, recovers below, big upper wick
    sweep_high = (
        high[-1] > prev_high and
        close[-1] < prev_high and
        wick_upper_pct >= wick_min_pct and
        body_pct <= 0.30 and
        volume[-1] > vol_avg * vol_mult and
        near_strict_bear_gp
    )

    return sweep_low, sweep_high

def detect_gps_divergences(wt1, wt2, high, low, rsi_values):
    """Detect regular bullish/bearish divergences using Wave Trend"""
    regular_bull_div = False
    regular_bear_div = False

    if len(wt1) < 10 or len(wt2) < 10:
        return regular_bull_div, regular_bear_div

    # Detect crossover/crossunder
    crossover = wt1[-1] > wt2[-1] and wt1[-2] <= wt2[-2] and wt1[-1] < -10
    crossunder = wt1[-1] < wt2[-1] and wt1[-2] >= wt2[-2] and wt1[-1] > 10

    if crossover:
        # Look for lower low in price but higher low in WT
        lookback = min(10, len(wt1) - 1)
        if lookback > 0:
            prev_low_idx = np.argmin(low[-lookback:])
            prev_low = low[-lookback + prev_low_idx] if prev_low_idx < len(low) - lookback else low[-lookback]
            if low[-1] < prev_low and wt1[-1] > wt1[-lookback + prev_low_idx] and rsi_values[-1] < 45:
                regular_bull_div = True

    if crossunder:
        # Look for higher high in price but lower high in WT
        lookback = min(10, len(wt1) - 1)
        if lookback > 0:
            prev_high_idx = np.argmax(high[-lookback:])
            prev_high = high[-lookback + prev_high_idx] if prev_high_idx < len(high) - lookback else high[-lookback]
            if high[-1] > prev_high and wt1[-1] < wt1[-lookback + prev_high_idx] and rsi_values[-1] > 55:
                regular_bear_div = True

    return regular_bull_div, regular_bear_div

def calculate_gps_confluence(df, gp_data, bullish_ob, bearish_ob, sweep_low, sweep_high,
                            regular_bull_div, regular_bear_div, vol_avg):
    """Calculate GPS confluence score"""
    current_price = df['close'].iloc[-1]
    volume = df['volume'].iloc[-1]

    confluence_score = 0.0
    confluence_factors = 0

    # GP proximity (20 pts for daily, 25 for weekly, 30 for monthly)
    if is_near_gp(current_price, gp_data['daily_gp_low'], gp_data['daily_gp_high'], 2.0):
        confluence_score += 20
        confluence_factors += 1

    if is_near_gp(current_price, gp_data['weekly_gp_low'], gp_data['weekly_gp_high'], 2.0):
        confluence_score += 25
        confluence_factors += 1

    if is_near_gp(current_price, gp_data['monthly_gp_low'], gp_data['monthly_gp_high'], 2.0):
        confluence_score += 30
        confluence_factors += 1

    # Heavy volume (20 pts)
    if volume > vol_avg * 0.8:
        confluence_score += 20
        confluence_factors += 1

    # Order blocks (16 pts)
    if bullish_ob or bearish_ob:
        confluence_score += 16
        confluence_factors += 1

    # Sweeps (18 pts)
    if sweep_low or sweep_high:
        confluence_score += 18
        confluence_factors += 1

    # Divergences (20 pts)
    if regular_bull_div or regular_bear_div:
        confluence_score += 20
        confluence_factors += 1

    # Cap at 100
    confluence_score = min(100, confluence_score)

    return confluence_score, confluence_factors

def gps_signal_grade(confluence_score, confluence_factors, two_of_three, near_strict_gp, heavy_volume):
    """Calculate GPS signal grade (A+, A, B)"""
    if confluence_score >= 75 and (two_of_three or (confluence_factors >= 4 and near_strict_gp and heavy_volume)):
        return "A+"
    elif confluence_score >= 65 and confluence_factors >= 4:
        return "A"
    elif confluence_score >= 55:
        return "B"
    return None

# ========================= PivotX Pro - Multi-Timeframe Pivots =========================

def detect_pivots_mtf(df, exchange, symbol, atr, atr_multiplier=0.5, min_strength=5):
    """
    Detect pivots across multiple timeframes (5m, 15m, 1h)
    Returns pivot data for each timeframe
    """
    pivots = {
        '5m': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None},
        '15m': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None},
        '1h': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None}
    }

    for tf in ['5m', '15m', '1h']:
        try:
            # Fetch data for this timeframe
            ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=200)
            if not ohlcv or len(ohlcv) < 50:
                continue

            ohlcv_arr = np.array(ohlcv)
            high = ohlcv_arr[:, 2]
            low = ohlcv_arr[:, 3]
            close = ohlcv_arr[:, 4]
            volume = ohlcv_arr[:, 5]

            # Calculate ATR for this timeframe
            tf_atr = np.mean(high[-14:] - low[-14:])

            # Dynamic pivot strength
            pivot_strength_raw = max(min_strength, int(tf_atr / (close[-1] * 0.0001) * atr_multiplier))
            pivot_strength = min(max(min_strength, pivot_strength_raw), 20)

            # Detect pivot highs and lows
            pivot_highs = []
            pivot_lows = []

            for i in range(pivot_strength, len(high) - pivot_strength):
                # Pivot high
                is_ph = True
                for j in range(i - pivot_strength, i + pivot_strength + 1):
                    if j == i:
                        continue
                    if high[j] >= high[i]:
                        is_ph = False
                        break
                if is_ph:
                    pivot_highs.append((i, high[i]))

                # Pivot low
                is_pl = True
                for j in range(i - pivot_strength, i + pivot_strength + 1):
                    if j == i:
                        continue
                    if low[j] <= low[i]:
                        is_pl = False
                        break
                if is_pl:
                    pivot_lows.append((i, low[i]))

            # Get last 2 pivots
            if pivot_highs:
                pivots[tf]['highs'] = [p[1] for p in pivot_highs[-2:]]
                pivots[tf]['last_ph'] = pivot_highs[-1][1]
            if pivot_lows:
                pivots[tf]['lows'] = [p[1] for p in pivot_lows[-2:]]
                pivots[tf]['last_pl'] = pivot_lows[-1][1]

        except Exception:
            continue

    return pivots

def detect_choch(pivots):
    """
    Detect Market Structure Shift (CHoCH - Change of Character)
    CHoCH Up: Higher PH and higher PL
    CHoCH Down: Lower PH and lower PL
    """
    choch_up = False
    choch_down = False

    for tf in ['5m', '15m', '1h']:
        if len(pivots[tf]['highs']) >= 2 and len(pivots[tf]['lows']) >= 2:
            ph_1, ph_2 = pivots[tf]['highs'][-2], pivots[tf]['highs'][-1]
            pl_1, pl_2 = pivots[tf]['lows'][-2], pivots[tf]['lows'][-1]

            # CHoCH Up: Higher high and higher low
            if ph_2 > ph_1 and pl_2 > pl_1:
                choch_up = True

            # CHoCH Down: Lower high and lower low
            if ph_2 < ph_1 and pl_2 < pl_1:
                choch_down = True

    return choch_up, choch_down

def detect_exhaustion(df, volume, vol_avg, exhaustion_periods=3, min_price_move=2.0):
    """
    Detect exhaustion signals:
    - Sell exhaustion: Price drop + volume spike + not rising
    - Buy exhaustion: Price rally + volume spike + not falling
    """
    if len(df) < exhaustion_periods + 1:
        return False, False

    current_price = df['close'].iloc[-1]
    price_periods_ago = df['close'].iloc[-exhaustion_periods-1]

    price_change_pct = ((current_price - price_periods_ago) / price_periods_ago) * 100

    vol_spike = volume[-1] > vol_avg * 1.5
    price_rising = current_price > df['close'].iloc[-2]
    price_falling = current_price < df['close'].iloc[-2]

    # Sell exhaustion: Price dropped significantly, volume spike, not rising
    sell_exhaustion = (
        price_change_pct <= -min_price_move and
        vol_spike and
        not price_rising
    )

    # Buy exhaustion: Price rallied significantly, volume spike, not falling
    buy_exhaustion = (
        price_change_pct >= min_price_move and
        vol_spike and
        not price_falling
    )

    return sell_exhaustion, buy_exhaustion

def check_pivot_zones(current_price, pivots, atr, tolerance_mult=0.3):
    """
    Check if price is near pivot zones (support/resistance)
    Returns: (near_support, near_resistance, pivot_level)
    """
    near_support = False
    near_resistance = False
    pivot_level = None

    for tf in ['5m', '15m', '1h']:
        tolerance = atr * tolerance_mult

        # Check pivot lows (support)
        if pivots[tf]['last_pl']:
            if abs(current_price - pivots[tf]['last_pl']) <= tolerance:
                near_support = True
                pivot_level = pivots[tf]['last_pl']

        # Check pivot highs (resistance)
        if pivots[tf]['last_ph']:
            if abs(current_price - pivots[tf]['last_ph']) <= tolerance:
                near_resistance = True
                if pivot_level is None:
                    pivot_level = pivots[tf]['last_ph']

    return near_support, near_resistance, pivot_level

# ========================= Tactical Deviation VWAP Logic =========================

def calculate_vwap_with_deviation(df, period_type='daily'):
    """
    Calculate VWAP with deviation bands (±1σ, ±2σ, ±3σ)
    period_type: 'daily', 'weekly', 'monthly'
    """
    hlc3 = (df['high'] + df['low'] + df['close']) / 3

    # Determine period boundaries
    if period_type == 'daily':
        # Group by day (approximate - use 24 hour windows)
        df['period'] = (df['timestamp'].dt.hour == 0).cumsum()
    elif period_type == 'weekly':
        # Group by week (approximate - use 168 hour windows)
        df['period'] = (df.index // 168)
    else:  # monthly
        # Group by month (approximate - use 720 hour windows)
        df['period'] = (df.index // 720)

    # Calculate VWAP per period
    df['pv'] = hlc3 * df['volume']
    df['pv2'] = (hlc3 ** 2) * df['volume']

    # Cumulative sums per period
    df['sum_pv'] = df.groupby('period')['pv'].cumsum()
    df['sum_v'] = df.groupby('period')['volume'].cumsum()
    df['sum_pv2'] = df.groupby('period')['pv2'].cumsum()

    # VWAP
    vwap = df['sum_pv'] / (df['sum_v'] + 1e-10)

    # Variance and Standard Deviation
    variance = (df['sum_pv2'] / (df['sum_v'] + 1e-10)) - (vwap ** 2)
    std_dev = np.sqrt(np.maximum(variance, 0))

    # Deviation bands
    upper1 = vwap + (std_dev * 1.0)
    lower1 = vwap - (std_dev * 1.0)
    upper2 = vwap + (std_dev * 2.0)
    lower2 = vwap - (std_dev * 2.0)
    upper3 = vwap + (std_dev * 3.0)
    lower3 = vwap - (std_dev * 3.0)

    return {
        'vwap': vwap.values,
        'upper1': upper1.values,
        'lower1': lower1.values,
        'upper2': upper2.values,
        'lower2': lower2.values,
        'upper3': upper3.values,
        'lower3': lower3.values,
        'std_dev': std_dev.values
    }

def get_deviation_level(price, vwap, std_dev, upper1, lower1, upper2, lower2, upper3, lower3):
    """Get current deviation level (0, 1, 2, or 3) and percentage"""
    if np.isnan(vwap) or std_dev == 0:
        return 0, 0.0

    dev_percent = ((price - vwap) / std_dev) if std_dev > 0 else 0.0
    level = 0

    if price >= upper3 or price <= lower3:
        level = 3
    elif price >= upper2 or price <= lower2:
        level = 2
    elif price >= upper1 or price <= lower1:
        level = 1

    return level, dev_percent

def detect_deviation_pullback(df, vwap_data, lookback=5):
    """
    Detect pullback to deviation bands for entry
    Returns: (is_pullback, deviation_level, is_super_exhausted)
    - 2±σ = A trade
    - 3±σ = A+ trade (super exhausted)
    """
    current_price = df['close'].iloc[-1]
    current_low = df['low'].iloc[-1]
    current_high = df['high'].iloc[-1]

    vwap = vwap_data['vwap'][-1]
    upper2 = vwap_data['upper2'][-1]
    lower2 = vwap_data['lower2'][-1]
    upper3 = vwap_data['upper3'][-1]
    lower3 = vwap_data['lower3'][-1]
    std_dev = vwap_data['std_dev'][-1]

    if np.isnan(vwap) or std_dev == 0:
        return False, 0, False

    # Check if price pulled back to deviation bands
    is_pullback = False
    deviation_level = 0
    is_super_exhausted = False

    # Check for pullback to lower bands (bullish entry)
    if current_low <= lower3 or (current_price <= lower3 and current_price > lower3 * 0.999):
        is_pullback = True
        deviation_level = 3
        is_super_exhausted = True  # 3σ = super exhausted = A+
    elif current_low <= lower2 or (current_price <= lower2 and current_price > lower2 * 0.999):
        is_pullback = True
        deviation_level = 2  # 2σ = A trade

    # Check for pullback to upper bands (bearish entry)
    elif current_high >= upper3 or (current_price >= upper3 and current_price < upper3 * 1.001):
        is_pullback = True
        deviation_level = 3
        is_super_exhausted = True  # 3σ = super exhausted = A+
    elif current_high >= upper2 or (current_price >= upper2 and current_price < upper2 * 1.001):
        is_pullback = True
        deviation_level = 2  # 2σ = A trade

    # Also check if price is currently at extreme deviation (not just pullback)
    current_level, current_dev_pct = get_deviation_level(
        current_price, vwap, std_dev,
        vwap_data['upper1'][-1], vwap_data['lower1'][-1],
        upper2, lower2, upper3, lower3
    )

    if current_level >= 3:
        is_super_exhausted = True
        deviation_level = max(deviation_level, 3)

    return is_pullback or current_level >= 2, deviation_level, is_super_exhausted

# ========================= Oath Keeper v2 - Major Divergences =========================

def calculate_money_flow(close: np.ndarray, volume: np.ndarray, length: int = 8) -> np.ndarray:
    """Calculate money flow index"""
    # Calculate up/down volume based on price direction
    up_vol = np.zeros_like(volume)
    down_vol = np.zeros_like(volume)

    for i in range(1, len(close)):
        if close[i] > close[i-1]:
            up_vol[i] = volume[i]
        elif close[i] < close[i-1]:
            down_vol[i] = volume[i]

    # Calculate rolling means using pandas
    up_series = pd.Series(up_vol)
    down_series = pd.Series(down_vol)

    mf_up = up_series.rolling(window=length, min_periods=1).mean().values
    mf_down = down_series.rolling(window=length, min_periods=1).mean().values

    # Calculate money flow
    money_flow = 100 * mf_up / (mf_up + mf_down + 1e-10)
    return money_flow

def detect_liquidation(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray, vol_avg: float) -> bool:
    """Enhanced liquidation detection"""
    current_vol = volume[-1]
    atr = np.mean(high[-14:] - low[-14:])
    current_high = high[-1]
    current_low = low[-1]
    current_close = close[-1]
    prev_close = close[-2] if len(close) >= 2 else close[-1]

    volume_spike = current_vol > vol_avg * 1.8
    wick_size = abs(current_high - current_low) > atr * 1.2
    price_jump = abs(current_close - prev_close) / prev_close > 0.008

    return volume_spike and wick_size and price_jump

def detect_macro_pivots(high: np.ndarray, low: np.ndarray, money_flow: np.ndarray, left: int = 6, right: int = 6):
    """Detect macro pivots (major pivots) for divergence analysis"""
    lookback = min(100, len(high))
    price_highs = []
    price_lows = []
    mf_highs = []
    mf_lows = []

    for i in range(left, lookback - right):
        # Price pivot high
        is_ph = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            if high[j] >= high[i]:
                is_ph = False
                break
        if is_ph:
            price_highs.append((i, high[i]))

        # Price pivot low
        is_pl = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            if low[j] <= low[i]:
                is_pl = False
                break
        if is_pl:
            price_lows.append((i, low[i]))

        # MF pivot high
        is_mfh = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            if money_flow[j] >= money_flow[i]:
                is_mfh = False
                break
        if is_mfh:
            mf_highs.append((i, money_flow[i]))

        # MF pivot low
        is_mfl = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            if money_flow[j] <= money_flow[i]:
                is_mfl = False
                break
        if is_mfl:
            mf_lows.append((i, money_flow[i]))

    # Get last 2 pivots
    price_highs = price_highs[-2:] if len(price_highs) >= 2 else []
    price_lows = price_lows[-2:] if len(price_lows) >= 2 else []
    mf_highs = mf_highs[-2:] if len(mf_highs) >= 2 else []
    mf_lows = mf_lows[-2:] if len(mf_lows) >= 2 else []

    return {
        'price_highs': [p[1] for p in price_highs],
        'price_lows': [p[1] for p in price_lows],
        'mf_highs': [p[1] for p in mf_highs],
        'mf_lows': [p[1] for p in mf_lows],
    }

def detect_major_divergences(high: np.ndarray, low: np.ndarray, money_flow: np.ndarray):
    """Detect major divergences (macro pivots) - focus for best confluence"""
    pivots = detect_macro_pivots(high, low, money_flow, left=6, right=6)

    reg_bull = False
    reg_bear = False
    hid_bull = False
    hid_bear = False

    # Regular Bullish: Lower price low, higher MF low
    if len(pivots['price_lows']) >= 2 and len(pivots['mf_lows']) >= 2:
        price_lower = pivots['price_lows'][-1] < pivots['price_lows'][-2]
        mf_higher = pivots['mf_lows'][-1] > pivots['mf_lows'][-2]
        reg_bull = price_lower and mf_higher

    # Regular Bearish: Higher price high, lower MF high
    if len(pivots['price_highs']) >= 2 and len(pivots['mf_highs']) >= 2:
        price_higher = pivots['price_highs'][-1] > pivots['price_highs'][-2]
        mf_lower = pivots['mf_highs'][-1] < pivots['mf_highs'][-2]
        reg_bear = price_higher and mf_lower

    # Hidden Bullish: Higher price low, lower MF low
    if len(pivots['price_lows']) >= 2 and len(pivots['mf_lows']) >= 2:
        price_higher = pivots['price_lows'][-1] > pivots['price_lows'][-2]
        mf_lower = pivots['mf_lows'][-1] < pivots['mf_lows'][-2]
        hid_bull = price_higher and mf_lower

    # Hidden Bearish: Lower price high, higher MF high
    if len(pivots['price_highs']) >= 2 and len(pivots['mf_highs']) >= 2:
        price_lower = pivots['price_highs'][-1] < pivots['price_highs'][-2]
        mf_higher = pivots['mf_highs'][-1] > pivots['mf_highs'][-2]
        hid_bear = price_lower and mf_higher

    return {
        'reg_bull': reg_bull,
        'reg_bear': reg_bear,
        'hid_bull': hid_bull,
        'hid_bear': hid_bear,
        'has_major_div': reg_bull or reg_bear or hid_bull or hid_bear
    }

# ========================= Simple Scanner =========================
class SimpleScanner:
    def __init__(self):
        self.exchanges = {
            'mexc': ccxt.mexc(),
            'bybit': ccxt.bybit(),
            'binance': ccxt.binance(),
        }

        # Load markets
        for name, ex in self.exchanges.items():
            try:
                ex.load_markets()
                print(f"[{name.upper()}] Loaded {len(ex.markets)} markets")
            except:
                pass

        self.signals_sent_this_hour = 0
        self.hour_start_time = time.time()
        # 2h cadence aligned to :30 based on ANCHOR_HOUR_ET
        self.scan_interval = SCAN_INTERVAL_SEC
        self.next_scan_due = self._compute_next_due()

    def _compute_next_due(self, from_ts: Optional[float] = None) -> float:
        """
        Find the next timestamp in ET where:
          minute == ALIGN_MINUTE and (hour - ANCHOR_HOUR_ET) % 2 == 0
        Returns UTC epoch seconds.
        """
        base_dt = datetime.now(TZ_NY) if from_ts is None else datetime.fromtimestamp(from_ts, TZ_NY)
        base_dt = base_dt.replace(second=0, microsecond=0)

        # Search forward up to 48h in 1-minute steps (DST-safe, simple)
        for i in range(0, 48*60):
            cand = base_dt + timedelta(minutes=i)
            if cand.minute == ALIGN_MINUTE and ((cand.hour - ANCHOR_HOUR_ET) % 2 == 0):
                return cand.astimezone(pytz.utc).timestamp()

        # Fallback: 2h from now
        return (datetime.now(pytz.utc) + timedelta(hours=2)).timestamp()

    def _bump_to_next_due(self):
        # compute from just after current due to keep cadence tight
        self.next_scan_due = self._compute_next_due(self.next_scan_due + 61)

    def get_best_exchange(self, symbol):
        """Find best exchange for a symbol"""
        for name, ex in self.exchanges.items():
            if symbol in ex.markets:
                return ex, name
        return None, None

    def scan_symbol(self, symbol):
        """Simple scan with basic indicators"""
        try:
            ex, ex_name = self.get_best_exchange(symbol)
            if not ex:
                return None

            # Fetch data
            ohlcv_1h = ex.fetch_ohlcv(symbol, '1h', limit=200)  # Need more data for GPS
            if not ohlcv_1h or len(ohlcv_1h) < 100:
                return None

            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Convert to arrays
            ohlcv = np.array(ohlcv_1h)
            high = ohlcv[:, 2]
            low = ohlcv[:, 3]
            close = ohlcv[:, 4]
            volume = ohlcv[:, 5]
            open_price = ohlcv[:, 1]

            current_price = close[-1]

            # Calculate basic indicators
            rsi_val = rsi(close)
            # Calculate RSI array for divergence detection
            rsi_array = np.full(len(close), 50.0)
            for i in range(14, len(close)):
                rsi_array[i] = rsi(close[:i+1])
            atr = np.mean(high[-14:] - low[-14:])
            vol_avg = np.mean(volume[-20:])

            # GPS (Golden Pocket Syndicate) Logic
            gp_data = calculate_golden_pockets(df)
            wt1, wt2 = calculate_wave_trend(high, low, close, n1=10, n2=21)
            bullish_ob, bearish_ob = detect_order_blocks(df, gp_data, vol_avg, atr)
            sweep_low, sweep_high = detect_sweeps(df, gp_data, vol_avg, atr)
            regular_bull_div, regular_bear_div = detect_gps_divergences(wt1, wt2, high, low, rsi_array)
            confluence_score, confluence_factors = calculate_gps_confluence(
                df, gp_data, bullish_ob, bearish_ob, sweep_low, sweep_high,
                regular_bull_div, regular_bear_div, vol_avg
            )

            # Check if near GP (strict)
            near_strict_bull_gp = (
                abs(current_price - gp_data['daily_gp_low']) / current_price < 0.01 or
                abs(current_price - gp_data['weekly_gp_low']) / current_price < 0.01 or
                abs(current_price - gp_data['monthly_gp_low']) / current_price < 0.01
            )
            near_strict_bear_gp = (
                abs(current_price - gp_data['daily_gp_high']) / current_price < 0.01 or
                abs(current_price - gp_data['weekly_gp_high']) / current_price < 0.01 or
                abs(current_price - gp_data['monthly_gp_high']) / current_price < 0.01
            )

            # Two of three: sweep, OB, or divergence
            two_of_three_bull = sum([sweep_low, bullish_ob, regular_bull_div]) >= 2
            two_of_three_bear = sum([sweep_high, bearish_ob, regular_bear_div]) >= 2

            heavy_volume = volume[-1] > vol_avg * 0.8

            # GPS signal grading
            gps_grade = gps_signal_grade(
                confluence_score, confluence_factors,
                two_of_three_bull or two_of_three_bear,
                near_strict_bull_gp or near_strict_bear_gp,
                heavy_volume
            )

            # Tactical Deviation VWAP - Pullback to Deviation Bands
            daily_vwap_data = calculate_vwap_with_deviation(df, 'daily')
            is_dev_pullback, dev_level, is_super_exhausted = detect_deviation_pullback(df, daily_vwap_data)

            # Deviation-based grade enhancement
            dev_grade = None
            if is_super_exhausted and dev_level >= 3:
                dev_grade = "A+"  # 3±σ = Super exhausted = A+
            elif is_dev_pullback and dev_level >= 2:
                dev_grade = "A"  # 2±σ = A trade

            # PivotX Pro - Multi-Timeframe Pivots (5m, 15m, 1h)
            try:
                pivots_mtf = detect_pivots_mtf(df, ex, symbol, atr, atr_multiplier=0.5, min_strength=5)
                choch_up, choch_down = detect_choch(pivots_mtf)
                sell_exhaustion, buy_exhaustion = detect_exhaustion(df, volume, vol_avg, exhaustion_periods=3, min_price_move=2.0)
                near_support, near_resistance, pivot_level = check_pivot_zones(current_price, pivots_mtf, atr, tolerance_mult=0.3)
            except Exception:
                # Fallback if pivot detection fails
                pivots_mtf = {'5m': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None},
                             '15m': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None},
                             '1h': {'highs': [], 'lows': [], 'last_ph': None, 'last_pl': None}}
                choch_up, choch_down = False, False
                sell_exhaustion, buy_exhaustion = False, False
                near_support, near_resistance, pivot_level = False, False, None

            # ATR confirmation for pivots
            atr_confirm_mult = 0.2
            atr_confirmed_pl = near_support and (close[-1] > pivot_level + (atr * atr_confirm_mult) if pivot_level else False)
            atr_confirmed_ph = near_resistance and (close[-1] < pivot_level - (atr * atr_confirm_mult) if pivot_level else False)

            # Oath Keeper v2 - Major Divergences
            money_flow = calculate_money_flow(close, volume, length=8)
            current_mf = money_flow[-1]
            prev_mf = money_flow[-2] if len(money_flow) >= 2 else current_mf

            # Detect major divergences (highest priority for confluence)
            divs = detect_major_divergences(high, low, money_flow)
            is_liquidation = detect_liquidation(high, low, close, volume, vol_avg)

            # Super Strong Signal Detection
            super_bull = (
                current_mf < 30 and
                current_mf > prev_mf and
                volume[-1] > vol_avg * 1.5 and
                (is_liquidation or (volume[-1] > vol_avg * 2 and
                 abs(close[-1] - low[-1]) / abs(high[-1] - low[-1]) > 0.7))
            )

            super_bear = (
                current_mf > 70 and
                current_mf < prev_mf and
                volume[-1] > vol_avg * 1.5 and
                (is_liquidation or (volume[-1] > vol_avg * 2 and
                 abs(high[-1] - close[-1]) / abs(high[-1] - low[-1]) > 0.7))
            )

            # Enhanced scoring with PivotX Pro + GPS + Deviation Bands + Oath Keeper
            score = 50.0
            signals = []

            # PIVOTX PRO - Multi-Timeframe Pivots (5m, 15m, 1h) - A+ Setup Enhancement
            pivot_bonus = 0
            if choch_up:
                score += 20
                signals.append("📈 CHoCH Up (5m/15m/1h)")
                pivot_bonus += 1
            if choch_down:
                score += 20
                signals.append("📉 CHoCH Down (5m/15m/1h)")
                pivot_bonus += 1

            # Exhaustion signals (strong reversal indicators)
            if sell_exhaustion:
                score += 18
                signals.append("🟢 Sell Exhaustion (Reversal Up)")
                pivot_bonus += 1
            if buy_exhaustion:
                score += 18
                signals.append("🔴 Buy Exhaustion (Reversal Down)")
                pivot_bonus += 1

            # Pivot zone confirmation
            if atr_confirmed_pl:
                score += 15
                signals.append("📊 Pivot Low Zone (ATR Confirmed)")
                pivot_bonus += 1
            if atr_confirmed_ph:
                score += 15
                signals.append("📊 Pivot High Zone (ATR Confirmed)")
                pivot_bonus += 1

            # Multi-timeframe pivot confluence (A+ setup)
            mtf_pivot_count = sum([1 for tf in ['5m', '15m', '1h'] if pivots_mtf[tf]['last_ph'] or pivots_mtf[tf]['last_pl']])
            if mtf_pivot_count >= 2:
                score += 12
                signals.append(f"🎯 MTF Pivot Confluence ({mtf_pivot_count}/3)")
                pivot_bonus += 1

            # TACTICAL DEVIATION - Pullback to Deviation Bands (Highest Priority for Entry)
            if is_super_exhausted and dev_level >= 3:
                score += 35
                signals.append(f"🔥 Super Exhausted @ 3±σ (A+)")
            elif is_dev_pullback and dev_level >= 2:
                score += 30
                signals.append(f"📉 Pullback @ 2±σ (A Trade)")

            # GPS SIGNALS - High priority
            if gps_grade:
                if gps_grade == "A+":
                    score += 30
                    signals.append(f"🎯 GPS {gps_grade} Signal")
                elif gps_grade == "A":
                    score += 25
                    signals.append(f"🎯 GPS {gps_grade} Signal")
                else:  # B
                    score += 20
                    signals.append(f"🎯 GPS {gps_grade} Signal")

            # GPS specific signals
            if bullish_ob:
                score += 18
                signals.append("📦 GPS Bullish OB")
            if bearish_ob:
                score += 18
                signals.append("📦 GPS Bearish OB")
            if sweep_low:
                score += 20
                signals.append("🧹 GPS Sweep Low HQ")
            if sweep_high:
                score += 20
                signals.append("🧹 GPS Sweep High HQ")
            if regular_bull_div or regular_bear_div:
                score += 18
                signals.append("📈 GPS Divergence")

            if confluence_score >= 70:
                score += 15
                signals.append(f"🔥 High Confluence ({confluence_score:.0f})")

            # MAJOR DIVERGENCE - Oath Keeper (white dots) - Best confluence
            if divs['has_major_div']:
                if divs['reg_bull'] or divs['hid_bull']:
                    score += 25
                    div_type = "Regular" if divs['reg_bull'] else "Hidden"
                    signals.append(f"⚪ Major Bullish Div ({div_type})")
                elif divs['reg_bear'] or divs['hid_bear']:
                    score += 25
                    div_type = "Regular" if divs['reg_bear'] else "Hidden"
                    signals.append(f"⚪ Major Bearish Div ({div_type})")

            # Super Strong Signals (liquidation + volume)
            elif super_bull:
                score += 20
                signals.append("⚡ Super Bull Signal")
            elif super_bear:
                score += 20
                signals.append("⚡ Super Bear Signal")

            # RSI conditions
            if rsi_val < 30:
                score += 15
                signals.append(f"RSI Oversold ({rsi_val:.0f})")
            elif rsi_val > 70:
                score += 15
                signals.append(f"RSI Overbought ({rsi_val:.0f})")

            # Oath Keeper basic signals (MF extremes)
            if current_mf < 30 and current_mf > prev_mf:
                score += 10
                signals.append(f"Oath Keeper Bull ({current_mf:.0f})")
            elif current_mf > 70 and current_mf < prev_mf:
                score += 10
                signals.append(f"Oath Keeper Bear ({current_mf:.0f})")

            # Volume spike
            if volume[-1] > vol_avg * 2.0:
                score += 10
                signals.append("Volume Spike")
            elif is_liquidation:
                score += 15
                signals.append("⚡ Liquidation Event")

            # Support/Resistance
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])

            if abs(current_price - recent_high) / current_price < 0.01:
                score += 8
                signals.append("Near Resistance")
            elif abs(current_price - recent_low) / current_price < 0.01:
                score += 8
                signals.append("Near Support")

            # Only return if score is high enough (75+)
            if score < 75:
                return None

            # Determine direction - Prioritize PivotX Pro + Deviation Pullbacks, then GPS, then Oath Keeper
            direction_found = False

            # Priority 1: PivotX Pro Exhaustion + CHoCH (A+ Setup)
            if sell_exhaustion and choch_up:
                side = "LONG"
                direction_found = True
            elif buy_exhaustion and choch_down:
                side = "SHORT"
                direction_found = True
            elif sell_exhaustion and near_support:
                side = "LONG"
                direction_found = True
            elif buy_exhaustion and near_resistance:
                side = "SHORT"
                direction_found = True

            # Priority 2: Deviation Band Pullbacks (BEST ENTRY - Super Exhausted)
            if not direction_found and is_dev_pullback:
                current_price = close[-1]
                vwap = daily_vwap_data['vwap'][-1]
                lower2 = daily_vwap_data['lower2'][-1]
                lower3 = daily_vwap_data['lower3'][-1]
                upper2 = daily_vwap_data['upper2'][-1]
                upper3 = daily_vwap_data['upper3'][-1]

                # Long entry: Pullback to lower deviation bands
                if (current_price <= lower3 or abs(current_price - lower3) / current_price < 0.01) or \
                   (current_price <= lower2 or abs(current_price - lower2) / current_price < 0.01):
                    side = "LONG"
                    direction_found = True
                # Short entry: Pullback to upper deviation bands
                elif (current_price >= upper3 or abs(current_price - upper3) / current_price < 0.01) or \
                     (current_price >= upper2 or abs(current_price - upper2) / current_price < 0.01):
                    side = "SHORT"
                    direction_found = True

            # Priority 3: GPS signals (high quality)
            if not direction_found and gps_grade and confluence_score >= 55:
                if (two_of_three_bull or (bullish_ob and near_strict_bull_gp) or (sweep_low and near_strict_bull_gp)):
                    side = "LONG"
                    direction_found = True
                elif (two_of_three_bear or (bearish_ob and near_strict_bear_gp) or (sweep_high and near_strict_bear_gp)):
                    side = "SHORT"
                    direction_found = True

            # Priority 3: Major divergences (Oath Keeper - white dots)
            if not direction_found and divs['has_major_div']:
                if (divs['reg_bull'] or divs['hid_bull']) and abs(current_price - recent_low) / current_price < 0.02:
                    side = "LONG"
                    direction_found = True
                elif (divs['reg_bear'] or divs['hid_bear']) and abs(current_price - recent_high) / current_price < 0.02:
                    side = "SHORT"
                    direction_found = True

            # Priority 4: Super strong signals
            if not direction_found and super_bull:
                side = "LONG"
                direction_found = True
            elif not direction_found and super_bear:
                side = "SHORT"
                direction_found = True

            # Priority 5: RSI + support/resistance
            if not direction_found:
                if rsi_val < 30 and abs(current_price - recent_low) / current_price < 0.01:
                    side = "LONG"
                    direction_found = True
                elif rsi_val > 70 and abs(current_price - recent_high) / current_price < 0.01:
                    side = "SHORT"
                    direction_found = True

            if not direction_found:
                return None

            # Calculate entry, stop loss, and take profit
            entry = current_price
            if side == "LONG":
                sl = current_price - atr * 1.5
                tp1 = current_price + atr * 2
                tp2 = current_price + atr * 4
            else:  # SHORT
                sl = current_price + atr * 1.5
                tp1 = current_price - atr * 2
                tp2 = current_price - atr * 4

            return {
                'symbol': symbol,
                'exchange': ex_name,
                'side': side,
                'entry': entry,
                'sl': sl,
                'tp1': tp1,
                'tp2': tp2,
                'score': score,
                'signals': signals,
                'rsi': rsi_val,
                'volume_ratio': volume[-1] / vol_avg if vol_avg > 0 else 1,
                'money_flow': current_mf,
                'major_div': divs['has_major_div'],
                'div_type': 'BULL' if (divs['reg_bull'] or divs['hid_bull']) else ('BEAR' if (divs['reg_bear'] or divs['hid_bear']) else None),
                'gps_grade': gps_grade,
                'gps_confluence': confluence_score,
                'gps_ob': bullish_ob or bearish_ob,
                'gps_sweep': sweep_low or sweep_high,
                'dev_pullback': is_dev_pullback,
                'dev_level': dev_level,
                'dev_grade': dev_grade,
                'super_exhausted': is_super_exhausted,
                'choch_up': choch_up,
                'choch_down': choch_down,
                'sell_exhaustion': sell_exhaustion,
                'buy_exhaustion': buy_exhaustion,
                'near_pivot_support': near_support,
                'near_pivot_resistance': near_resistance,
                'mtf_pivot_count': mtf_pivot_count
            }

        except Exception as e:
            return None

    def scan_all_coins(self):
        """Scan all prioritized coins"""
        opportunities = []

        # Scan top macro coins first
        for symbol in TOP_MACRO_COINS:
            result = self.scan_symbol(symbol)
            if result:
                opportunities.append(result)

        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities

    def adaptive_scan(self):
        """Scan only when the aligned 2h due-time arrives; limit 3 signals per hour."""
        now = time.time()
        if now < self.next_scan_due:
            return None

        # Reset signal counter every hour
        if now - self.hour_start_time >= 3600:
            self.signals_sent_this_hour = 0
            self.hour_start_time = now

        if self.signals_sent_this_hour >= 3:
            # Even if rate-limited, move to the next aligned window
            self._bump_to_next_due()
            return None

        # Perform scan now (we're at/after due time)
        opportunities = self.scan_all_coins()
        # Schedule next aligned run
        self._bump_to_next_due()

        if opportunities:
            high_quality = [o for o in opportunities if o['score'] >= 80]
            watchlist = [o for o in opportunities if 70 <= o['score'] < 80]
            return {
                'high_quality': high_quality,
                'watchlist': watchlist,
                'total': len(opportunities)
            }
        else:
            return None

# ========================= Discord Formatting =========================
def create_trade_card(trade):
    """Create formatted Discord embed for trades"""
    # Long = Green, Short = Purple (always, even with major div)
    color = 0x00ff00 if trade['side'] == 'LONG' else 0x800080
    emoji = "🟢" if trade['side'] == 'LONG' else "🟣"

    # Highlight major divergences (white dot emoji, but keep green/purple colors)
    if trade.get('major_div'):
        emoji = "⚪"  # White dot for major divergence

    # Get TradingView link
    tv_link = get_tradingview_link(trade['symbol'])

    # Build description
    desc = f"**Score:** {trade['score']}/100\n**Exchange:** {trade['exchange']}"

    # PivotX Pro - Multi-Timeframe Pivots (A+ Setup)
    pivotx_signals = []
    if trade.get('choch_up'):
        pivotx_signals.append("📈 CHoCH Up")
    if trade.get('choch_down'):
        pivotx_signals.append("📉 CHoCH Down")
    if trade.get('sell_exhaustion'):
        pivotx_signals.append("🟢 Sell Exhaustion")
    if trade.get('buy_exhaustion'):
        pivotx_signals.append("🔴 Buy Exhaustion")
    if trade.get('mtf_pivot_count', 0) >= 2:
        pivotx_signals.append(f"🎯 MTF Pivots ({trade.get('mtf_pivot_count', 0)}/3)")

    if pivotx_signals:
        desc += f"\n{' • '.join(pivotx_signals)}"

    # Deviation Pullback (Best Entry)
    if trade.get('super_exhausted'):
        desc += f"\n🔥 **SUPER EXHAUSTED @ 3±σ (A+)**"
    elif trade.get('dev_pullback') and trade.get('dev_level', 0) >= 2:
        desc += f"\n📉 **Pullback @ 2±σ (A Trade)**"

    # GPS Grade
    if trade.get('gps_grade'):
        desc += f"\n🎯 **GPS {trade['gps_grade']} Signal**"
        if trade.get('gps_confluence'):
            desc += f" • Confluence: {trade['gps_confluence']:.0f}%"

    # Major Divergence (Oath Keeper)
    if trade.get('major_div'):
        desc += f"\n⚪ **Major Divergence** ({trade.get('div_type', 'N/A')})"

    desc += f"\n\n📈 [TradingView Chart]({tv_link})"

    # Build indicators line
    indicators = f"RSI: {trade['rsi']:.0f} | Vol: {trade['volume_ratio']:.1f}x"
    if 'money_flow' in trade:
        indicators += f" | MF: {trade['money_flow']:.0f}"
    if trade.get('gps_ob'):
        indicators += " | 📦 OB"
    if trade.get('gps_sweep'):
        indicators += " | 🧹 Sweep"

    return {
        "title": f"{emoji} {trade['symbol']} - {trade['side']}",
        "description": desc,
        "color": color,
        "fields": [
            {
                "name": "📊 Entry",
                "value": f"${trade['entry']:.6f}",
                "inline": True
            },
            {
                "name": "🛑 Stop Loss",
                "value": f"${trade['sl']:.6f}",
                "inline": True
            },
            {
                "name": "🎯 Targets",
                "value": f"TP1: ${trade['tp1']:.6f}\nTP2: ${trade['tp2']:.6f}",
                "inline": True
            },
            {
                "name": "📈 Signals",
                "value": " + ".join(trade['signals'][:3]),
                "inline": False
            },
            {
                "name": "📊 Indicators",
                "value": indicators,
                "inline": False
            }
        ],
        "footer": {
            "text": f"MCRO Scanner • {trade['exchange'].upper()}" +
                   (f" • GPS {trade.get('gps_grade', '')}" if trade.get('gps_grade') else "") +
                   (" • Major Div ⚪" if trade.get('major_div') else "")
        },
        "timestamp": datetime.now(TZ_NY).isoformat()
    }

def create_watchlist_embed(watchlist):
    """Create watchlist embed"""
    fields = []

    for trade in watchlist[:3]:  # Show top 3 only
        emoji = "🟢" if trade['side'] == 'LONG' else "🟣"
        tv_link = get_tradingview_link(trade['symbol'])
        fields.append({
            "name": f"{emoji} {trade['symbol']}",
            "value": f"Score: {trade['score']}/100\n{trade['side']} @ ${trade['entry']:.6f}\n[📈 Chart]({tv_link})",
            "inline": True
        })

    return {
        "title": "👀 Watchlist (7-8/10 Quality)",
        "description": "Potential setups developing",
        "color": 0xffa500,
        "fields": fields,
        "footer": {
            "text": "MCRO Scanner • Watchlist"
        },
        "timestamp": datetime.now(TZ_NY).isoformat()
    }

# ========================= Main Loop =========================
def main():
    print("🚀 MCRO Bot - Signals Only • 2h Aligned Cadence")
    print("=" * 50)

    scanner = SimpleScanner()

    # Initial notification
    next_due_dt = datetime.fromtimestamp(scanner.next_scan_due, pytz.utc).astimezone(TZ_NY)
    post_discord("", {
        "title": "🤖 MCRO Scanner Started",
        "description": f"Scanning top {len(TOP_MACRO_COINS)} macro coins",
        "color": 0x00bfff,
        "fields": [
            {"name": "📊 Mode", "value": "Signals Only", "inline": True},
            {"name": "⏰ Frequency", "value": "Every 2 Hours (aligned)", "inline": True},
            {"name": "🕰️ Next Run (ET)", "value": next_due_dt.strftime("%Y-%m-%d %H:%M"), "inline": True},
        ],
        "timestamp": datetime.now(TZ_NY).isoformat()
    })

    last_status_update = 0

    while True:
        try:
            # Adaptive scanning
            scan_result = scanner.adaptive_scan()

            if scan_result:
                signals_sent = 0

                # Process high quality trades (8-10/10) - MAX 3 trades per hour
                if scan_result['high_quality'] and scanner.signals_sent_this_hour < 3:
                    for trade in scan_result['high_quality'][:3]:  # Limit to 3 trades max
                        if scanner.signals_sent_this_hour >= 3:
                            break
                        embed = create_trade_card(trade)
                        post_discord("", embed)
                        scanner.signals_sent_this_hour += 1
                        signals_sent += 1
                        time.sleep(2)  # Add delay between trades

                # Show watchlist (7-8/10) - Only if we haven't sent 3 signals yet
                if scan_result['watchlist'] and scanner.signals_sent_this_hour < 3:
                    remaining_signals = 3 - scanner.signals_sent_this_hour
                    watchlist_embed = create_watchlist_embed(scan_result['watchlist'][:remaining_signals])
                    post_discord("", watchlist_embed)
                    scanner.signals_sent_this_hour += 1
                    signals_sent += 1

                print(f"[SCAN] Found {scan_result['total']} opportunities, sent {signals_sent} signals")

            # Status update every 6 hours
            current_time = time.time()
            if current_time - last_status_update > 21600:
                next_due_dt = datetime.fromtimestamp(scanner.next_scan_due, pytz.utc).astimezone(TZ_NY)
                mins_till = int(max(0, (scanner.next_scan_due - current_time) // 60))
                status_embed = {
                    "title": "📊 Scanner Status",
                    "description": "Active • 2h aligned cadence",
                    "color": 0x00bfff,
                    "fields": [
                        {"name": "⏰ Signals This Hour", "value": f"{scanner.signals_sent_this_hour}/3", "inline": True},
                        {"name": "🕰️ Next Run (ET)", "value": next_due_dt.strftime("%Y-%m-%d %H:%M"), "inline": True},
                        {"name": "⏳ In", "value": f"~{mins_till} min", "inline": True},
                    ],
                    "timestamp": datetime.now(TZ_NY).isoformat()
                }
                post_discord("", status_embed)
                last_status_update = current_time

            # Sleep for 1 minute before next check
            time.sleep(60)

        except KeyboardInterrupt:
            print("\n[SHUTDOWN] Scanner stopped")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
