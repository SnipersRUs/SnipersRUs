#!/usr/bin/env python3

# Degen Hunter — Bitunix Spot (Top-3 + 3 Watch, max 3 trades per 2.5-hour scan, 2.5-hour loop)

import os, json, time, random
from datetime import datetime, timezone
from typing import List, Dict, Optional
import numpy as np, pandas as pd, requests, ccxt

class BitunixAdapter:
    """Bitunix exchange adapter (ccxt-compatible interface)"""
    def __init__(self, config=None):
        self.config = config or {}
        self.id = "bitunix"
        # Try multiple potential base URLs
        self.base_urls = [
            "https://openapi.bitunix.com",
            "https://api.bitunix.com",
            "https://www.bitunix.com/api"
        ]
        self.base_url = self.base_urls[0]
        self.markets = {}
        self._markets_loaded = False

    def load_markets(self):
        """Load all spot markets from Bitunix"""
        # Try different API endpoint variations
        endpoints = [
            "/open/api/v1/symbols",
            "/api/v1/symbols",
            "/api/v1/markets",
            "/v1/public/symbols",
            "/public/v1/symbols"
        ]

        for base_url in self.base_urls:
            for endpoint in endpoints:
                try:
                    url = f"{base_url}{endpoint}"
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        self.base_url = base_url
                        self.markets = {}

                        # Handle different response formats
                        symbols_list = []
                        if isinstance(data, dict):
                            symbols_list = data.get("data", data.get("result", data.get("symbols", [])))
                        elif isinstance(data, list):
                            symbols_list = data

                        for sym in symbols_list:
                            # Handle different symbol formats
                            if isinstance(sym, dict):
                                quote = sym.get("quoteCurrency") or sym.get("quote") or sym.get("quoteAsset")
                                base = sym.get("baseCurrency") or sym.get("base") or sym.get("baseAsset")
                                market_type = sym.get("marketType") or sym.get("type") or sym.get("market")
                                status = sym.get("status") or sym.get("state")
                            elif isinstance(sym, str):
                                # Format: "BTC_USDT" or "BTC/USDT"
                                parts = sym.replace("_", "/").split("/")
                                if len(parts) == 2:
                                    base, quote = parts
                                    market_type = "spot"  # Assume spot if not specified
                                    status = "TRADING"
                                else:
                                    continue
                            else:
                                continue

                            if quote == "USDT" and (market_type == "spot" or market_type is None):
                                symbol = f"{base}/USDT"
                                self.markets[symbol] = {
                                    "base": base,
                                    "quote": "USDT",
                                    "symbol": symbol,
                                    "spot": True,
                                    "active": status == "TRADING" if status else True
                                }

                        self._markets_loaded = True
                        if len(self.markets) > 0:
                            print(f"✅ Bitunix markets loaded: {len(self.markets)} spot pairs")
                            return self.markets
                        else:
                            print(f"⚠️ Bitunix API responded but no spot markets found")
                            return {}
                except Exception as e:
                    continue

        print("⚠️ Could not connect to Bitunix API. Please verify API endpoints.")
        print("   Using fallback: will try to fetch data per symbol")
        return {}

    def fetch_ticker(self, symbol):
        """Fetch ticker data for a symbol"""
        base = symbol.split("/")[0]
        endpoints = [
            f"/open/api/v1/ticker",
            f"/api/v1/ticker",
            f"/v1/ticker",
            f"/public/v1/ticker"
        ]

        symbol_formats = [f"{base}_USDT", f"{base}/USDT", f"{base}USDT"]

        for endpoint in endpoints:
            for sym_format in symbol_formats:
                try:
                    url = f"{self.base_url}{endpoint}"
                    params = {"symbol": sym_format}
                    r = requests.get(url, params=params, timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        # Handle different response formats
                        if isinstance(data, dict):
                            ticker_data = data.get("data", data.get("result", data))
                            last = float(ticker_data.get("lastPrice") or ticker_data.get("last") or ticker_data.get("close") or 0)
                            vol_24h = float(ticker_data.get("volume") or ticker_data.get("baseVolume") or 0)
                            change_pct = float(ticker_data.get("priceChangePercent") or ticker_data.get("changePercent") or ticker_data.get("percentage") or 0)
                            if last > 0:
                                return {
                                    "last": last,
                                    "close": last,
                                    "quoteVolume": vol_24h * last if vol_24h else 0,
                                    "baseVolume": vol_24h,
                                    "percentage": change_pct
                                }
                except:
                    continue
        return {"last": 0, "close": 0, "quoteVolume": 0, "baseVolume": 0, "percentage": 0}

    def fetch_ohlcv(self, symbol, timeframe="15m", limit=220):
        """Fetch OHLCV data"""
        base = symbol.split("/")[0]
        tf_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        tf = tf_map.get(timeframe, "15m")

        endpoints = [
            f"/open/api/v1/klines",
            f"/api/v1/klines",
            f"/v1/klines",
            f"/public/v1/klines",
            f"/open/api/v1/candles",
            f"/api/v1/candles"
        ]

        symbol_formats = [f"{base}_USDT", f"{base}/USDT", f"{base}USDT"]

        for endpoint in endpoints:
            for sym_format in symbol_formats:
                try:
                    url = f"{self.base_url}{endpoint}"
                    params = {
                        "symbol": sym_format,
                        "interval": tf,
                        "limit": limit
                    }
                    r = requests.get(url, params=params, timeout=15)
                    if r.status_code == 200:
                        data = r.json()
                        # Handle different response formats
                        if isinstance(data, dict):
                            bars = data.get("data", data.get("result", data.get("klines", [])))
                        elif isinstance(data, list):
                            bars = data
                        else:
                            continue

                        if bars and len(bars) > 0:
                            ohlcv = []
                            for bar in bars:
                                if isinstance(bar, list) and len(bar) >= 6:
                                    ohlcv.append([
                                        int(bar[0]),  # timestamp (ms)
                                        float(bar[1]),  # open
                                        float(bar[2]),  # high
                                        float(bar[3]),  # low
                                        float(bar[4]),  # close
                                        float(bar[5])   # volume
                                    ])
                            if len(ohlcv) > 0:
                                return ohlcv
                except:
                    continue
        return []

class CFG:
    TF = "15m"
    SCAN_LIMIT = 1200
    MAX_WORKERS = 6
    MIN_VOL = 100_000          # ignore dead coins
    MAX_VOL = 20_000_000
    RSI_BAND = (24, 48)        # bottom zone
    MAX_BB_WIDTH = 0.18        # squeeze-ish
    MAX_ABS_CHG = 12           # calm last 24h
    TOP = 3
    WATCH = 3
    START_BAL = 10_000.0
    BASE_SIZE = 500.0
    MAX_OPEN = 3
    STOP_PCT = 0.25
    TP1, TP2, TP3 = 0.10, 0.40, 1.00
    TP1_FR, TP2_FR = 0.4, 0.4
    COOLDOWN = 3600
    LOOP_SECS = 9000           # 2.5 hours (2 hours 30 minutes)
    WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1433390367369072652/4hSOGIkaE8Zj9AQWHekaBcy_2wbzHdp3IvBCxYyD5-oCrRhV9UGgP0AF-lpi0Zn_NAWI")
    COLORS = {"HEADER":0xFF1493,"BOTTOM":0x00FF00,"ACC":0xFFA500,"WATCH":0xF39C12,"WHITE":0xFFFFFF,"GREEN":0x2ECC71,"BLUE":0x3498DB}

def now_utc(): return datetime.now(timezone.utc)

def _clean_base_symbol(b):
    """Clean base symbol to avoid double USDT (e.g., DUCKUSDTUSDT -> DUCK)"""
    base = str(b).upper().strip()
    # Split on / or _ and take first part
    if "/" in base:
        base = base.split("/")[0]
    if "_" in base:
        base = base.split("_")[0]
    # Remove ALL occurrences of USDT (handles DUCKUSDTUSDT case)
    base = base.replace("USDT", "").strip()
    return base

def bitunix_link(b):
    base = _clean_base_symbol(b)
    return f"https://www.bitunix.com/exchange/{base}_USDT"

def tv_link(b):
    # Format should be just TICKER/USDT (e.g., DUCKUSDT or use exchange format)
    # TradingView will handle the symbol lookup automatically
    base = _clean_base_symbol(b)
    return f"https://www.tradingview.com/chart/?symbol={base}USDT"

def x_link(b):  return f"https://twitter.com/search?q=%24{b}&src=typed_query&f=live"

def post_embeds(embeds: List[Dict]):
    if not CFG.WEBHOOK: print("No webhook set"); return
    nfa={"title":"⚠️ DEGEN — Not Financial Advice","description":"High-volatility spot plays. Use stops.","color":0xFF0000}
    try:
        r=requests.post(CFG.WEBHOOK, json={"embeds":[nfa]+embeds[:9]}, timeout=15)
        if r.status_code!=204: print("Webhook HTTP", r.status_code, r.text[:200])
    except Exception as e: print("Webhook err:",e)

def rsi(s, n=14):
    d=s.diff(); up=d.clip(lower=0).rolling(n).mean(); dn=(-d.clip(upper=0)).rolling(n).mean()
    rs=up/dn.replace(0,np.nan); return 100-(100/(1+rs))

def bb_width(s, n=20, std=2):
    if len(s)<n+1: return 9.9
    m=s.rolling(n).mean(); sd=s.rolling(n).std()
    up,lo=m+std*sd, m-std*sd
    return float((up.iloc[-1]-lo.iloc[-1]) / max(1e-12, m.iloc[-1]))

class GPSIndicator:
    """Golden Pocket Syndicate (GPS) Indicator - Enhanced version from Pine Script"""

    def __init__(self, n1=10, n2=21, sensitivity=3, ob_confirm_bars=6, sweep_lookback=36):
        self.n1 = n1  # WT Channel Length
        self.n2 = n2  # WT Average Length
        self.sensitivity = sensitivity
        self.ob_confirm_bars = ob_confirm_bars
        self.sweep_lookback = sweep_lookback
        self.pivot_lookback = 5

    def calculate_wave_trend(self, df):
        """Calculate Wave Trend indicator (WT1 and WT2)"""
        ap = (df['high'] + df['low']) / 2  # Average price
        esa = ap.ewm(span=self.n1, adjust=False).mean()  # EMA Smoothing Average
        d = abs(ap - esa).ewm(span=self.n1, adjust=False).mean()  # Delta
        ci = (ap - esa) / (0.015 * d.replace(0, np.nan))  # Chande Index
        wt1 = ci.ewm(span=self.n2, adjust=False).mean()
        wt2 = wt1.rolling(4).mean()
        return wt1, wt2

    def calculate_golden_pockets(self, df):
        """Calculate Daily, Weekly, Monthly Golden Pockets (0.618-0.65 retracement)"""
        gp = {}

        # Daily GP (current day) - ensure float conversion
        daily_high = float(df['high'].max())
        daily_low = float(df['low'].min())
        gp['daily_gp_high'] = float(daily_high - (daily_high - daily_low) * 0.618)
        gp['daily_gp_low'] = float(daily_high - (daily_high - daily_low) * 0.65)

        # Weekly GP (approximate with available data)
        if len(df) >= 168:
            weekly_high = float(df['high'].tail(168).max())
            weekly_low = float(df['low'].tail(168).min())
        else:
            weekly_high = daily_high
            weekly_low = daily_low
        gp['weekly_gp_high'] = float(weekly_high - (weekly_high - weekly_low) * 0.618)
        gp['weekly_gp_low'] = float(weekly_high - (weekly_high - weekly_low) * 0.65)

        # Monthly GP (approximate with available data)
        if len(df) >= 720:
            monthly_high = float(df['high'].tail(720).max())
            monthly_low = float(df['low'].tail(720).min())
        else:
            monthly_high = weekly_high
            monthly_low = weekly_low
        gp['monthly_gp_high'] = float(monthly_high - (monthly_high - monthly_low) * 0.618)
        gp['monthly_gp_low'] = float(monthly_high - (monthly_high - monthly_low) * 0.65)

        return gp

    def detect_order_blocks(self, df, gp_data, ob_tighten_pct=5, ob_atr_mult=0.75, ob_range_atr=1.0,
                           ob_body_min=0.42, ob_vol_mult=1.20, ob_require_fvg=True, ob_require_gp=False):
        """Detect bullish/bearish order blocks with improved logic"""
        c, h, l, v, o = df['close'], df['high'], df['low'], df['volume'], df['open']
        atr = (h - l).rolling(14).mean()
        vol_avg = v.rolling(20).mean()
        body = abs(c - o)
        body_pct = body / (h - l).replace(0, 1e-10)
        range_size = h - l

        # Get previous swing highs/lows
        pivot_lookback = self.pivot_lookback
        prev_swing_high = h.rolling(pivot_lookback).max().shift(1)
        prev_swing_low = l.rolling(pivot_lookback).min().shift(1)

        # BOS detection
        bos_up = h.rolling(self.ob_confirm_bars).max() > prev_swing_high
        bos_down = l.rolling(self.ob_confirm_bars).min() < prev_swing_low

        # FVG detection
        bull_fvg = l > h.shift(2)
        bear_fvg = h < l.shift(2)

        # Tighten multiplier
        tighten = 1.0 + ob_tighten_pct / 100.0

        # Base conditions for bullish OB
        bull_base = (
            bos_up &
            (c < o) &  # Bearish candle
            (body >= atr * ob_atr_mult * tighten) &
            (range_size >= atr * ob_range_atr) &
            (v > vol_avg * ob_vol_mult) &
            (body_pct >= min(0.95, ob_body_min * tighten))
        )

        # Apply FVG requirement if needed
        if ob_require_fvg:
            bull_base = bull_base & bull_fvg

        # Apply GP requirement if needed
        if ob_require_gp:
            gp_check = pd.Series([
                self._is_near_gp(float(price_val), gp_data, bullish=True)
                for price_val in c
            ], index=c.index)
            bull_base = bull_base & gp_check

        # Base conditions for bearish OB
        bear_base = (
            bos_down &
            (c > o) &  # Bullish candle
            (body >= atr * ob_atr_mult * tighten) &
            (range_size >= atr * ob_range_atr) &
            (v > vol_avg * ob_vol_mult) &
            (body_pct >= min(0.95, ob_body_min * tighten))
        )

        # Apply FVG requirement if needed
        if ob_require_fvg:
            bear_base = bear_base & bear_fvg

        # Apply GP requirement if needed
        if ob_require_gp:
            gp_check = pd.Series([
                self._is_near_gp(float(price_val), gp_data, bullish=False)
                for price_val in c
            ], index=c.index)
            bear_base = bear_base & gp_check

        bullish_ob = bull_base
        bearish_ob = bear_base

        return bullish_ob.iloc[-1] if len(bullish_ob) > 0 and bullish_ob.iloc[-1] else False, \
               bearish_ob.iloc[-1] if len(bearish_ob) > 0 and bearish_ob.iloc[-1] else False

    def detect_sweeps(self, df, gp_data, sweep_wick_min_pct=0.65, sweep_body_max_pct=0.30,
                     sweep_vol_mult=1.35, sweep_atr_frac=0.20, sweeps_must_be_at_gp=True):
        """Detect high-quality liquidity sweeps"""
        c, h, l, v, o = df['close'], df['high'], df['low'], df['volume'], df['open']
        atr = (h - l).rolling(14).mean()
        vol_avg = v.rolling(20).mean()

        # Calculate wicks and body percentages
        range_size = h - l
        wick_lower = (o.min(c) - l) / range_size.replace(0, 1e-10)
        wick_upper = (h - o.max(c)) / range_size.replace(0, 1e-10)
        body_pct = abs(c - o) / range_size.replace(0, 1e-10)

        # Previous extremes
        prev_low_n = l.rolling(self.sweep_lookback).min().shift(1)
        prev_high_n = h.rolling(self.sweep_lookback).max().shift(1)

        # Exceed previous extremes by ATR fraction
        exceed_low = (prev_low_n - l) >= atr * sweep_atr_frac
        exceed_high = (h - prev_high_n) >= atr * sweep_atr_frac

        # Sweep conditions
        sweep_l_base = (
            (l < prev_low_n) &
            exceed_low &
            (c > prev_low_n) &
            (wick_lower >= sweep_wick_min_pct) &
            (body_pct <= sweep_body_max_pct) &
            (v > vol_avg * sweep_vol_mult)
        )

        sweep_h_base = (
            (h > prev_high_n) &
            exceed_high &
            (c < prev_high_n) &
            (wick_upper >= sweep_wick_min_pct) &
            (body_pct <= sweep_body_max_pct) &
            (v > vol_avg * sweep_vol_mult)
        )

        # Context check (must be near GP if required)
        if sweeps_must_be_at_gp:
            # Apply GP check element-wise for pandas Series
            sweep_l_ctx_ok = pd.Series([
                self._is_near_gp(float(price_val), gp_data, bullish=True, strict=True)
                for price_val in c
            ], index=c.index)
            sweep_h_ctx_ok = pd.Series([
                self._is_near_gp(float(price_val), gp_data, bullish=False, strict=True)
                for price_val in c
            ], index=c.index)
        else:
            sweep_l_ctx_ok = pd.Series([True] * len(df), index=df.index)
            sweep_h_ctx_ok = pd.Series([True] * len(df), index=df.index)

        swept_lows_hq = sweep_l_base & sweep_l_ctx_ok
        swept_highs_hq = sweep_h_base & sweep_h_ctx_ok

        return swept_lows_hq.iloc[-1] if len(swept_lows_hq) > 0 else False, \
               swept_highs_hq.iloc[-1] if len(swept_highs_hq) > 0 else False

    def detect_divergences(self, df, wt1, wt2):
        """Detect regular bullish/bearish divergences"""
        c, h, l = df['close'], df['high'], df['low']
        rsi_vals = rsi(c)

        # Find pivot points
        pivot_high = h.rolling(5, center=True).max()
        pivot_low = l.rolling(5, center=True).min()
        is_pivot_high = h == pivot_high
        is_pivot_low = l == pivot_low

        regular_bull_div = False
        regular_bear_div = False

        # Regular bullish divergence: lower price low, higher WT low
        if is_pivot_low.tail(10).any():
            last_lows = c[is_pivot_low].tail(2)
            last_wt_lows = wt1[is_pivot_low].tail(2)
            if len(last_lows) >= 2 and len(last_wt_lows) >= 2:
                regular_bull_div = (
                    last_lows.iloc[-1] < last_lows.iloc[-2] and
                    last_wt_lows.iloc[-1] > last_wt_lows.iloc[-2] and
                    rsi_vals.iloc[-1] < 45
                )

        # Regular bearish divergence: higher price high, lower WT high
        if is_pivot_high.tail(10).any():
            last_highs = c[is_pivot_high].tail(2)
            last_wt_highs = wt1[is_pivot_high].tail(2)
            if len(last_highs) >= 2 and len(last_wt_highs) >= 2:
                regular_bear_div = (
                    last_highs.iloc[-1] > last_highs.iloc[-2] and
                    last_wt_highs.iloc[-1] < last_wt_highs.iloc[-2] and
                    rsi_vals.iloc[-1] > 55
                )

        return regular_bull_div, regular_bear_div

    def calculate_confluence(self, df, gp_data, bullish_ob, bearish_ob, swept_lows, swept_highs,
                           regular_bull_div, regular_bear_div, min_confluence=55):
        """Calculate confluence score (0-100)"""
        c = df['close']
        v = df['volume']
        current_price = float(c.iloc[-1])  # Ensure it's a float, not a Series
        vol_avg = v.rolling(20).mean()
        heavy_volume = float(v.iloc[-1]) > float(vol_avg.iloc[-1]) * 0.8

        confluence_score = 0.0
        confluence_factors = 0

        # GP proximity (20/25/30 points)
        if self._is_near_gp(current_price, gp_data, daily=True):
            confluence_score += 20
            confluence_factors += 1
        if self._is_near_gp(current_price, gp_data, weekly=True):
            confluence_score += 25
            confluence_factors += 1
        if self._is_near_gp(current_price, gp_data, monthly=True):
            confluence_score += 30
            confluence_factors += 1

        # Heavy volume (20 pts)
        if heavy_volume:
            confluence_score += 20
            confluence_factors += 1

        # Order blocks (16 pts)
        if bullish_ob or bearish_ob:
            confluence_score += 16
            confluence_factors += 1

        # Sweeps (18 pts)
        if swept_lows or swept_highs:
            confluence_score += 18
            confluence_factors += 1

        # Divergences (20 pts)
        if regular_bull_div or regular_bear_div:
            confluence_score += 20
            confluence_factors += 1

        # Trend alignment (10 pts)
        ema_short = c.ewm(span=50, adjust=False).mean()
        ema_long = c.ewm(span=200, adjust=False).mean()
        ema_short_val = float(ema_short.iloc[-1])
        ema_long_val = float(ema_long.iloc[-1])
        trend_align = (current_price > ema_short_val and current_price > ema_long_val) or \
                      (current_price < ema_short_val and current_price < ema_long_val)
        if trend_align:
            confluence_score += 10
            confluence_factors += 1

        confluence_score = min(100, confluence_score) if confluence_factors > 0 else 0

        return int(confluence_score), confluence_factors >= min_confluence

    def _is_near_gp(self, price, gp_data, bullish=True, strict=False, daily=False, weekly=False, monthly=False, gp_range_pct=2.0):
        """Check if price is near a Golden Pocket zone"""
        tolerance = (gp_range_pct / 100.0) * 0.5 if strict else (gp_range_pct / 100.0)

        if daily or not (weekly or monthly):
            near_daily = abs(price - gp_data['daily_gp_low']) / price < tolerance or \
                        abs(price - gp_data['daily_gp_high']) / price < tolerance
            if near_daily:
                return True

        if weekly:
            near_weekly = abs(price - gp_data['weekly_gp_low']) / price < tolerance or \
                          abs(price - gp_data['weekly_gp_high']) / price < tolerance
            if near_weekly:
                return True

        if monthly:
            near_monthly = abs(price - gp_data['monthly_gp_low']) / price < tolerance or \
                           abs(price - gp_data['monthly_gp_high']) / price < tolerance
            if near_monthly:
                return True

        # Check all if not specified
        if not (daily or weekly or monthly):
            all_near = (
                abs(price - gp_data['daily_gp_low']) / price < tolerance or
                abs(price - gp_data['daily_gp_high']) / price < tolerance or
                abs(price - gp_data['weekly_gp_low']) / price < tolerance or
                abs(price - gp_data['weekly_gp_high']) / price < tolerance or
                abs(price - gp_data['monthly_gp_low']) / price < tolerance or
                abs(price - gp_data['monthly_gp_high']) / price < tolerance
            )
            return all_near

        return False

def load_state():
    path="degen_state.json"
    if not os.path.exists(path):
        return {"paper":{"start":CFG.START_BAL,"balance":CFG.START_BAL,"trades":[],"stats":{"wins":0,"losses":0,"pnl":0.0},"cooldown_until":0,"scan_period_start":time.time(),"trades_this_scan":0},"last_valid":{}}
    state = json.load(open(path))
    # Initialize scan period tracking if missing
    if "scan_period_start" not in state["paper"]:
        state["paper"]["scan_period_start"] = time.time()
    if "trades_this_scan" not in state["paper"]:
        state["paper"]["trades_this_scan"] = 0
    return state

def save_state(s): json.dump(s, open("degen_state.json","w"), indent=2)

class Scanner:
    def __init__(self):
        self.ex=None
        self.gps = GPSIndicator()  # Initialize GPS indicator
    def init(self):
        # Try multiple exchanges for reliable spot market data
        # Priority: OKX > Kraken > Gate.io (Bitunix API not publicly accessible)
        exchanges_to_try = [
            ("okx", "OKX"),
            ("kraken", "Kraken"),
            ("gate", "Gate.io")
        ]

        for ex_id, ex_name in exchanges_to_try:
            try:
                exchange_class = getattr(ccxt, ex_id)
                self.ex = exchange_class({"enableRateLimit":True,"timeout":20000})
                self.ex.load_markets()
                print(f"✅ Exchange connected (using {ex_name} for market data)")
                return
            except Exception as e:
                print(f"⚠️ {ex_name} failed: {str(e)[:100]}")
                continue

        raise Exception("Could not connect to any exchange. Please check your network connection.")
    def spot_only(self):
        spot,fut=set(),set()
        for _,m in self.ex.markets.items():
            if m.get("quote")=="USDT" and m.get("active"):
                if m.get("spot"): spot.add(m.get("base"))
                if m.get("swap"): fut.add(m.get("base"))
        bases=sorted([b for b in spot if b not in fut])
        print(f"Spot-only bases: {len(bases)}")
        return bases
    def ticker(self, b):
        try:
            t=self.ex.fetch_ticker(f"{b}/USDT")
            last=float(t.get("last") or t.get("close") or 0.0)
            qv=float(t.get("quoteVolume") or 0.0)
            if qv<=0: qv=float(t.get("baseVolume") or 0.0)*last
            chg=float(t.get("percentage") or 0.0)
            return last,qv,chg
        except: return 0.0,0.0,0.0
    def ohlcv(self,b,tf=CFG.TF,limit=220):
        try:
            o=self.ex.fetch_ohlcv(f"{b}/USDT", tf, limit=limit)
            if not o or len(o)<80: return None
            return pd.DataFrame(o, columns=["ts","open","high","low","close","volume"])
        except: return None
    def score(self,b):
        price,vol,chg=self.ticker(b)
        if price<=0 or vol<CFG.MIN_VOL or vol>CFG.MAX_VOL: return None
        df=self.ohlcv(b);
        if df is None or len(df)<100: return None

        c,h,l,v,o=df["close"],df["high"],df["low"],df["volume"],df["open"]

        # Calculate GPS indicators
        try:
            # Calculate Golden Pockets
            gp_data = self.gps.calculate_golden_pockets(df)

            # Calculate Wave Trend
            wt1, wt2 = self.gps.calculate_wave_trend(df)

            # Detect Order Blocks
            bullish_ob, bearish_ob = self.gps.detect_order_blocks(df, gp_data)

            # Detect Sweeps
            swept_lows, swept_highs = self.gps.detect_sweeps(df, gp_data)

            # Detect Divergences
            regular_bull_div, regular_bear_div = self.gps.detect_divergences(df, wt1, wt2)

            # Calculate Confluence
            confluence_score, passes_confluence = self.gps.calculate_confluence(
                df, gp_data, bullish_ob, bearish_ob, swept_lows, swept_highs,
                regular_bull_div, regular_bear_div, min_confluence=55
            )

        except Exception as e:
            print(f"⚠️ GPS calculation error for {b}: {e}")
            # Fallback to basic scoring
            return self._basic_score(df, b, price, vol, chg)

        # Enhanced scoring with GPS signals
        recent_high = float(h.iloc[-120:].max())
        dd = (c.iloc[-1]/recent_high-1)*100 if recent_high else -0.0
        r = float(rsi(c).iloc[-1])
        width = bb_width(c)
        burst = (v.iloc[-3:].mean() / max(1e-9, v.iloc[-30:].mean()))

        # Base score from original logic
        s = 0
        if dd <= -28: s += 25
        if CFG.RSI_BAND[0] <= r <= CFG.RSI_BAND[1]: s += 25
        if width < CFG.MAX_BB_WIDTH: s += 18
        if burst > 1.3: s += 18
        if abs(chg) < CFG.MAX_ABS_CHG: s += 10

        # Add GPS bonus points
        gps_bonus = 0
        if confluence_score >= 75: gps_bonus += 20
        elif confluence_score >= 55: gps_bonus += 10
        if bullish_ob or bearish_ob: gps_bonus += 8
        if swept_lows or swept_highs: gps_bonus += 8
        if regular_bull_div or regular_bear_div: gps_bonus += 7

        final_score = min(100, s + gps_bonus)

        # Determine strategy type
        if width < 0.12 and burst > 1.2:
            strategy = "ACCUMULATION"
        elif confluence_score >= 70:
            strategy = "GPS_HIGH_CONFLUENCE"
        elif dd <= -28 and confluence_score >= 55:
            strategy = "GPS_BOTTOM_ZONE"
        else:
            strategy = "BOTTOM"

        return {
            "base": b,
            "symbol": f"{b}/USDT",
            "price": float(c.iloc[-1]),
            "vol_24h": vol,
            "change_24h": chg,
            "dd": float(dd),
            "rsi": r,
            "bb_width": width,
            "burst": burst,
            "score": int(final_score),
            "strategy": strategy,
            "confluence": confluence_score,
            "gps_signals": {
                "bullish_ob": bullish_ob,
                "bearish_ob": bearish_ob,
                "swept_lows": swept_lows,
                "swept_highs": swept_highs,
                "bull_div": regular_bull_div,
                "bear_div": regular_bear_div
            }
        }

    def _basic_score(self, df, b, price, vol, chg):
        """Fallback basic scoring if GPS fails"""
        c,h,l,v=df["close"],df["high"],df["low"],df["volume"]
        recent_high=float(h.iloc[-120:].max())
        dd=(c.iloc[-1]/recent_high-1)*100 if recent_high else -0.0
        r=float(rsi(c).iloc[-1]); width=bb_width(c)
        burst = (v.iloc[-3:].mean() / max(1e-9, v.iloc[-30:].mean()))
        s=0
        if dd<=-28: s+=25
        if CFG.RSI_BAND[0]<=r<=CFG.RSI_BAND[1]: s+=25
        if width<CFG.MAX_BB_WIDTH: s+=18
        if burst>1.3: s+=18
        if abs(chg)<CFG.MAX_ABS_CHG: s+=10
        kind="ACCUMULATION" if width<0.12 and burst>1.2 else "BOTTOM"
        return {"base":b,"symbol":f"{b}/USDT","price":float(c.iloc[-1]),"vol_24h":vol,"change_24h":chg,
                "dd":float(dd),"rsi":r,"bb_width":width,"burst":burst,"score":int(min(100,s)),"strategy":kind}
    def scan(self):
        bases=self.spot_only(); random.shuffle(bases); bases=bases[:CFG.SCAN_LIMIT]
        out=[]
        for b in bases:
            r=self.score(b)
            if r: out.append(r)
            time.sleep(0.01)
        out.sort(key=lambda x:(x["score"], x["burst"], -abs(x["change_24h"])), reverse=True)
        sig=out[:CFG.TOP]
        used=set(o["base"] for o in sig)
        watch=[o for o in out if o["base"] not in used][:CFG.WATCH]
        return sig, watch

class Trader:
    def __init__(self, state, scanner): self.s=state; self.sc=scanner
    def cooldown(self): return time.time()<self.s["paper"]["cooldown_until"]
    def reset_scan_period_if_needed(self):
        """Reset scan period and trade counter every 2.5 hours"""
        p = self.s["paper"]
        now = time.time()
        if now - p.get("scan_period_start", 0) >= CFG.LOOP_SECS:
            p["scan_period_start"] = now
            p["trades_this_scan"] = 0
            save_state(self.s)
    def maybe_open(self, signals, embeds):
        self.reset_scan_period_if_needed()
        p=self.s["paper"]; open_cnt=sum(1 for t in p["trades"] if t["status"]=="open")
        # Limit to 3 trades per scan period (2.5 hours)
        scan_trades_remaining = 3 - p.get("trades_this_scan", 0)
        # Also respect max open positions
        position_cap = CFG.MAX_OPEN - open_cnt
        cap = min(scan_trades_remaining, position_cap)
        if cap<=0 or self.cooldown(): return
        for s in signals:
            if cap<=0: break
            if any(t["status"]=="open" and t["base"]==s["base"] for t in p["trades"]): continue
            if s["score"]<80: continue
            self.open_trade(s, embeds); cap-=1
    def open_trade(self, s, embeds):
        p=self.s["paper"]; e=s["price"]; qty=CFG.BASE_SIZE/e; stop=e*(1-CFG.STOP_PCT)
        t={"id":f"{s['base']}-{int(time.time())}","base":s["base"],"symbol":s["symbol"],"entry":e,"qty":qty,"init_qty":qty,
           "stop":stop,"tp1":False,"tp2":False,"status":"open","opened_at":time.time()}
        p["trades"].append(t)
        p["trades_this_scan"] = p.get("trades_this_scan", 0) + 1
        embeds.append({"title":f"🟢 ENTRY — {s['base']}/USDT","description":f"Entry **{e:.10f}** • Stop **{stop:.10f}** • Size **{qty:.6f}**\nTPs: 10% / 40% / 100%\n[TV]({tv_link(s['base'])}) • [X]({x_link(s['base'])})","color":0x8A2BE2})
        save_state(self.s)
    def manage(self, embeds):
        p=self.s["paper"]; ex=self.sc.ex; status=[]
        for t in p["trades"]:
            if t["status"]!="open": continue
            px=float(ex.fetch_ticker(t["symbol"]).get("last") or t["entry"])
            e=t["entry"]
            if px<=t["stop"]: self.close(t, px, "STOP", embeds); continue
            if (not t["tp1"]) and px>=e*1.10: self.partial(t, px, CFG.TP1_FR, "TP1 +10%", embeds); t["stop"]=max(t["stop"], e)
            if (not t["tp2"]) and px>=e*1.40: self.partial(t, px, CFG.TP2_FR, "TP2 +40%", embeds); t["stop"]=max(t["stop"], e*1.10)
            if px>=e*2.00: self.close(t, px, "TP3 +100%", embeds); continue
            upct=(px/e-1)*100
            status.append(f"• **{t['base']}** entry {e:.10f} now {px:.10f} P/L {upct:+.2f}% size {t['qty']:.6f} stop {t['stop']:.10f} {'TP1✓' if t['tp1'] else ''} {'TP2✓' if t['tp2'] else ''}")
        if status: embeds.append({"title":"📊 Open Trades","description":"\n".join(status)+f"\n\nBalance: ${p['balance']:,.2f}","color":CFG.COLORS["GREEN"]})
    def partial(self, t, px, frac, tag, embeds):
        p=self.s["paper"]; q=t["qty"]*frac; t["qty"]-=q;
        if tag.startswith("TP1"): t["tp1"]=True
        if tag.startswith("TP2"): t["tp2"]=True
        pnl=(px-t["entry"])*q; p["balance"]+=pnl; p["stats"]["pnl"]+=pnl
        embeds.append({"title":f"✅ {tag} — {t['base']}","description":f"Closed {frac*100:.0f}% @ {px:.10f}\nRealized **${pnl:,.2f}**\nRemain {t['qty']:.6f} • Balance ${p['balance']:,.2f}","color":CFG.COLORS["GREEN"]})
    def close(self, t, px, reason, embeds):
        p=self.s["paper"]; q=t["qty"]; pnl=(px-t["entry"])*q
        p["balance"]+=pnl; p["stats"]["pnl"]+=pnl
        t["qty"]=0; t["status"]="closed";
        if pnl>0: p["stats"]["wins"]+=1
        else: p["stats"]["losses"]+=1
        embeds.append({"title":f"🧾 Closed — {t['base']}","description":f"Reason: **{reason}**\nExit {px:.10f}\nRealized **${pnl:,.2f}**\nBalance **${p['balance']:,.2f}**","color":CFG.COLORS["BLUE"]})

def header(p):
    return {"title":"💗 DEGEN HUNTER — Spot Trading (Top-3)","description":f"Time: {now_utc().strftime('%Y-%m-%d %H:%M UTC')} • Scanned spot-only\nStart: ${p['start']:,.2f} • Current: ${p['balance']:,.2f} • W/L: {p['stats']['wins']}/{p['stats']['losses']} • PnL: ${p['stats']['pnl']:,.2f}","color":CFG.COLORS["HEADER"]}

def sig_card(s,i):
    # Determine color based on strategy and GPS signals
    strategy = s.get("strategy", "BOTTOM")
    if "GPS_HIGH_CONFLUENCE" in strategy:
        color = CFG.COLORS["GREEN"]
    elif strategy == "ACCUMULATION":
        color = CFG.COLORS["ACC"]
    else:
        color = CFG.COLORS["BOTTOM"]

    # Build GPS signals info
    gps_info = ""
    if "confluence" in s:
        gps_info += f"Confluence: **{s['confluence']}/100** • "
    if "gps_signals" in s:
        signals = s["gps_signals"]
        active = []
        if signals.get("bullish_ob") or signals.get("bearish_ob"): active.append("OB")
        if signals.get("swept_lows") or signals.get("swept_highs"): active.append("Sweep")
        if signals.get("bull_div") or signals.get("bear_div"): active.append("Div")
        if active:
            gps_info += f"GPS: {', '.join(active)} • "

    d=(f"Price: **${s['price']:.10f}** • Vol24: **${s['vol_24h']:,.0f}** • 24h: **{s['change_24h']:+.1f}%**\n"
       f"Score: **{s['score']}/100** • Type: **{strategy}**\n"
       f"{gps_info}DD: **{s['dd']:.1f}%** • RSI: **{s['rsi']:.1f}** • BBw: **{s['bb_width']:.3f}** • Burst× **{s['burst']:.2f}**\n"
       f"[TV]({tv_link(s['base'])}) • [X]({x_link(s['base'])})")
    return {"title":f"#{i} — {s['base']}/USDT","description":d,"color":color}

def watch_card(wl):
    if not wl: return {"title":"👀 Watchlist","description":"No extras this scan","color":CFG.COLORS["WATCH"]}
    lines=[]
    for w in wl:
        calm="calm 24h" if abs(w["change_24h"])<6 else f"{w['change_24h']:+.1f}% 24h"
        lines.append(f"• **{w['base']}** — {w['score']}/100 • ${w['price']:.10f} • Vol ${w['vol_24h']:,.0f} • DD {w['dd']:.0f}% • BBw {w['bb_width']:.3f} • Burst× {w['burst']:.2f} • {calm} • [TV]({tv_link(w['base'])}) • [X]({x_link(w['base'])})")
    return {"title":"👀 Watchlist — Low-cap potential movers","description":"\n".join(lines),"color":CFG.COLORS["WATCH"]}

def once():
    state=load_state(); sc=Scanner(); sc.init(); tr=Trader(state, sc)
    sigs,wl=sc.scan()
    embeds=[header(state["paper"])]
    if sigs:
        for i,s in enumerate(sigs,1): embeds.append(sig_card(s,i))
    else:
        embeds.append({"title":"No high-conviction signals","description":"Watching for better bottom coils…","color":CFG.COLORS["WHITE"]})
    embeds.append(watch_card(wl))
    tr.manage(embeds)
    tr.maybe_open(sigs, embeds)
    post_embeds(embeds)
    save_state(state)
    print(f"signals {len(sigs)}  •  watch {len(wl)}")

def run(loop=False, interval=CFG.LOOP_SECS):
    once()
    if loop:
        while True:
            time.sleep(max(600, interval))
            once()

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=CFG.LOOP_SECS)
    args=ap.parse_args()
    run(loop=args.loop, interval=args.interval)
