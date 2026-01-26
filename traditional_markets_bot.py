"""
Traditional Markets Breakout Bot
Applies GPS + Head Hunter + Oath Keeper logic to stocks, futures, and forex

Uses free APIs with fallbacks:
- yfinance (primary, free but rate-limited)
- Alpha Vantage (free tier: 500 calls/day)
- Polygon.io (free tier: 5 calls/min)
- Finnhub (free tier: 60 calls/min)
- Stooq (no API key needed)

.env required:
  WEBHOOK=<discord webhook>
  ALPHA_VANTAGE_API=<optional>
  POLYGON_API=<optional>
  FINNHUB_API=<optional>
  SCAN_INTERVAL=60
  ACCOUNT_SIZE=10000
"""

import os
import json
import time
import math
import warnings
import io
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional
import requests
import pandas as pd
import numpy as np
import feedparser
import yfinance as yf
import certifi
import schedule
import pytz
from dotenv import load_dotenv

# News feeds
NEWS_FEEDS = [
    ("Macro", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("Stocks", "https://www.investing.com/rss/news_25.rss"),
    ("Futures", "https://www.investing.com/rss/commodities.rss"),
    ("FX", "https://www.investing.com/rss/news_22.rss"),
    ("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
]

warnings.filterwarnings("ignore")
pd.options.mode.chained_assignment = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traditional_markets_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load env
load_dotenv()

WEBHOOK = os.getenv("WEBHOOK", "").strip()
ALPHA_VANTAGE_API = os.getenv("ALPHA_VANTAGE_API", "").strip()
POLYGON_API = os.getenv("POLYGON_API", "").strip()
FINNHUB_API = os.getenv("FINNHUB_API", "").strip()
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 14400))  # Default 4 hours (14400 seconds)
ACCOUNT_SIZE = float(os.getenv("ACCOUNT_SIZE", 10000))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 0.015))

# Embed colors
COLOR_WHITE = 0xFFFFFF
COLOR_BLUE = 0x1E90FF
COLOR_ORANGE = 0xFFA500
COLOR_RED = 0xCC3333
COLOR_GREEN = 0x00FF00

STATE_FILE = "traditional_markets_state.json"
CA_BUNDLE = certifi.where()

# Polite headers
UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Default universes
STOCKS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "AMD", "TSLA", "GOOGL", "PLTR", "IONQ", "RKLB"]
FUTURES = ["ES=F", "NQ=F", "YM=F", "CL=F", "GC=F"]
FOREX = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X"]

# ETF proxies for futures if direct feed fails
FUTS_PROXY = {"ES=F": "SPY", "NQ=F": "QQQ", "YM=F": "DIA", "CL=F": "USO", "GC=F": "GLD"}

# API rate limiting
_api_call_times = {
    "alphavantage": [],
    "polygon": [],
    "finnhub": []
}


# ========== HTTP SESSION ==========
_session = None


def http():
    """Shared Requests session with CA bundle"""
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update(UA_HEADERS)
        s.verify = CA_BUNDLE
        _session = s
    return _session


def can_call_api(provider: str, max_calls: int, window_seconds: int) -> bool:
    """Check if we can make an API call (rate limiting)"""
    now = time.time()
    calls = _api_call_times[provider]
    # Remove calls outside window
    calls[:] = [t for t in calls if now - t < window_seconds]
    return len(calls) < max_calls


def record_api_call(provider: str):
    """Record an API call for rate limiting"""
    _api_call_times[provider].append(time.time())


def now_utc():
    return datetime.now(timezone.utc)


def is_saturday() -> bool:
    """Check if today is Saturday"""
    return datetime.now(timezone.utc).weekday() == 5  # 5 = Saturday


def is_sunday() -> bool:
    """Check if today is Sunday"""
    return datetime.now(timezone.utc).weekday() == 6  # 6 = Sunday


def is_market_open(symbol: str) -> bool:
    """Check if market is open for trading based on symbol type"""
    et = pytz.timezone('America/New_York')
    now_et = datetime.now(et)
    weekday = now_et.weekday()  # 0=Monday, 6=Sunday

    # Weekend - markets closed
    if weekday >= 5:  # Saturday or Sunday
        return False

    # Check symbol type
    if "=X" in symbol:  # Forex
        # Forex is open 24/5 (Sunday 5pm ET - Friday 5pm ET)
        # But we'll be conservative and only trade during main sessions
        hour = now_et.hour
        # Main forex hours: 8 AM - 5 PM ET
        return 8 <= hour < 17

    elif "=F" in symbol:  # Futures
        # Futures have extended hours, but main session is 9:30 AM - 4:00 PM ET
        hour = now_et.hour
        minute = now_et.minute
        # Regular trading hours: 9:30 AM - 4:00 PM ET
        if hour == 9:
            return minute >= 30
        return 10 <= hour < 16

    else:  # Stocks
        # Stock market hours: 9:30 AM - 4:00 PM ET
        hour = now_et.hour
        minute = now_et.minute
        if hour == 9:
            return minute >= 30
        return 10 <= hour < 16

    return False


def get_week_start() -> datetime:
    """Get the start of the current week (Sunday)"""
    now = datetime.now(timezone.utc)
    days_since_sunday = now.weekday() + 1  # Monday=0, so +1 to get days since Sunday
    if days_since_sunday == 7:  # It's Sunday
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=days_since_sunday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def pull_news(n: int = 6, max_age_hours: int = 24) -> List[Tuple[str, str, str, str]]:
    """Pull recent news headlines from RSS feeds - only fresh news with links"""
    out = []
    now = datetime.now(timezone.utc)
    seen_titles = set()  # Track seen headlines to avoid duplicates

    for tag, url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:3]:  # Check more entries to find fresh ones
                # Get published date
                pub_date = None
                if hasattr(e, 'published_parsed') and e.published_parsed:
                    try:
                        pub_date = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
                    except:
                        pass
                elif hasattr(e, 'updated_parsed') and e.updated_parsed:
                    try:
                        pub_date = datetime(*e.updated_parsed[:6], tzinfo=timezone.utc)
                    except:
                        pass

                # Skip if too old
                if pub_date:
                    age_hours = (now - pub_date).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        continue

                title = e.title.replace("\n", " ").strip()[:200]
                title_lower = title.lower()

                # Skip duplicates
                if title_lower in seen_titles:
                    continue
                seen_titles.add(title_lower)

                # Get link
                link = getattr(e, 'link', '') or getattr(e, 'id', '')

                # Add with timestamp and link
                out.append((tag, title, pub_date.isoformat() if pub_date else "unknown", link))
                if len(out) >= n:
                    return out
        except Exception as e:
            logger.debug(f"News feed error {tag}: {e}")
            continue
    return out


def tv_link(sym: str) -> str:
    """Generate TradingView link"""
    fmap = {
        "ES=F": "CME_MINI:ES1!",
        "NQ=F": "CME_MINI:NQ1!",
        "YM=F": "CBOT_MINI:YM1!",
        "CL=F": "NYMEX:CL1!",
        "GC=F": "COMEX:GC1!"
    }
    if sym in fmap:
        return f"https://www.tradingview.com/chart/?symbol={fmap[sym]}"
    if sym.endswith("=X"):
        return f"https://www.tradingview.com/chart/?symbol=OANDA:{sym.replace('=X', '')}"
    return f"https://www.tradingview.com/chart/?symbol={sym}"


# ========== DATA PROVIDERS (Multi-fallback) ==========

def fetch_yahoo(sym: str, period: str = "59d", interval: str = "1h") -> pd.DataFrame:
    """Primary: yfinance"""
    try:
        # Don't pass session - yfinance handles it internally
        t = yf.Ticker(sym)
        df = t.history(period=period, interval=interval, auto_adjust=True, prepost=True)
        if df.empty:
            logger.warning(f"[yahoo] {sym}: Empty dataframe")
            return pd.DataFrame()
        # Normalize column names to lowercase
        df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
        # Ensure we have required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required):
            logger.warning(f"[yahoo] {sym}: Missing columns. Got: {df.columns.tolist()}")
            return pd.DataFrame()
        # Select only required columns and drop NaN
        df = df[required].dropna(how="any")
        if len(df) < 50:
            logger.warning(f"[yahoo] {sym}: Only {len(df)} rows, need at least 50")
            return pd.DataFrame()
        return df
    except Exception as e:
        logger.error(f"[yahoo] {sym}: {e}")
        return pd.DataFrame()


def fetch_alpha_vantage(sym: str, interval: str = "60min") -> pd.DataFrame:
    """Alpha Vantage free tier: 500 calls/day"""
    if not ALPHA_VANTAGE_API or not can_call_api("alphavantage", 1, 60):
        return pd.DataFrame()

    try:
        # Remove =X suffix for stocks
        symbol_clean = sym.replace("=X", "").replace("=F", "")

        # Alpha Vantage uses different endpoints
        if "=" in sym:  # Futures/Forex
            return pd.DataFrame()

        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY" if interval != "1d" else "TIME_SERIES_DAILY",
            "symbol": symbol_clean,
            "interval": interval,
            "apikey": ALPHA_VANTAGE_API,
            "outputsize": "full"
        }

        r = http().get(url, params=params, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        record_api_call("alphavantage")

        # Parse response
        key = [k for k in data.keys() if "Time Series" in k]
        if not key:
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(data[key[0]], orient="index")
        df.index = pd.to_datetime(df.index)
        df.columns = ["open", "high", "low", "close", "volume"]
        df = df.astype(float).sort_index()
        return df[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        logger.debug(f"[alphavantage] {sym}: {e}")
        return pd.DataFrame()


def fetch_polygon(sym: str, interval: str = "1h") -> pd.DataFrame:
    """Polygon.io free tier: 5 calls/min"""
    if not POLYGON_API or not can_call_api("polygon", 5, 60):
        return pd.DataFrame()

    try:
        symbol_clean = sym.replace("=X", "").replace("=F", "")

        # Convert interval
        multiplier = "1" if interval == "1h" else "1440"  # daily
        timespan = "hour" if interval == "1h" else "day"

        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol_clean}/range/{multiplier}/{timespan}"
        params = {
            "from": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d"),
            "apiKey": POLYGON_API,
            "limit": 5000
        }

        r = http().get(url, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        record_api_call("polygon")

        if data.get("status") != "OK" or not data.get("results"):
            return pd.DataFrame()

        # Parse results
        results = data["results"]
        df = pd.DataFrame(results)
        df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df.rename(columns={
            "o": "open", "h": "high", "l": "low",
            "c": "close", "v": "volume"
        }, inplace=True)
        return df[["open", "high", "low", "close", "volume"]].sort_index()
    except Exception as e:
        logger.debug(f"[polygon] {sym}: {e}")
        return pd.DataFrame()


def fetch_finnhub(sym: str, resolution: str = "60") -> pd.DataFrame:
    """Finnhub free tier: 60 calls/min"""
    if not FINNHUB_API or not can_call_api("finnhub", 60, 60):
        return pd.DataFrame()

    try:
        symbol_clean = sym.replace("=X", "").replace("=F", "")

        # Convert interval
        res_map = {"1h": "60", "1d": "D"}
        res = res_map.get(resolution, "60")

        to_ts = int(time.time())
        from_ts = int((datetime.now() - timedelta(days=60)).timestamp())

        url = f"https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": symbol_clean,
            "resolution": res,
            "from": from_ts,
            "to": to_ts,
            "token": FINNHUB_API
        }

        r = http().get(url, params=params, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        record_api_call("finnhub")

        if data.get("s") != "ok" or not data.get("c"):
            return pd.DataFrame()

        # Parse candles
        df = pd.DataFrame({
            "open": data["o"],
            "high": data["h"],
            "low": data["l"],
            "close": data["c"],
            "volume": data["v"]
        })
        df.index = pd.to_datetime(data["t"], unit="s")
        return df.sort_index()
    except Exception as e:
        logger.debug(f"[finnhub] {sym}: {e}")
        return pd.DataFrame()


def fetch_stooq(sym: str, tf: str = "1h") -> pd.DataFrame:
    """Stooq fallback (no API key)"""
    try:
        s = sym.lower().replace("=x", "").replace("=f", "").replace(".", "")
        i = "60" if tf in ("1h", "60m") else "d"
        url = f"https://stooq.com/q/d/l/?s={s}&i={i}"

        r = http().get(url, timeout=15)
        if r.status_code != 200 or not r.text.strip():
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(r.text))
        if df.empty:
            return df

        # Parse timestamp
        ts = (pd.to_datetime(df["Date"] + " " + df["Time"])
              if "Time" in df.columns
              else pd.to_datetime(df["Date"]))
        df.index = ts
        df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        }, inplace=True)
        return df[["open", "high", "low", "close", "volume"]].dropna(how="any")
    except Exception as e:
        logger.debug(f"[stooq] {sym}: {e}")
        return pd.DataFrame()


def fetch_one(sym: str, period: str = "59d", interval: str = "1h") -> pd.DataFrame:
    """Fetch with multiple fallbacks"""
    # Try yfinance first
    df = fetch_yahoo(sym, period, interval)
    if not df.empty:
        return df

    # Try Alpha Vantage
    df = fetch_alpha_vantage(sym, interval)
    if not df.empty:
        return df

    # Try Polygon
    df = fetch_polygon(sym, interval)
    if not df.empty:
        return df

    # Try Finnhub
    df = fetch_finnhub(sym, interval)
    if not df.empty:
        return df

    # Try ETF proxy for futures
    if sym in FUTS_PROXY:
        proxy = FUTS_PROXY[sym]
        df = fetch_yahoo(proxy, period, interval)
        if not df.empty:
            df["symbol_proxy"] = proxy
            return df

    # Final fallback: Stooq
    return fetch_stooq(sym, interval)


def fetch_realtime_price(sym: str) -> Optional[float]:
    """Get real-time price with fallbacks"""
    try:
        # Try yfinance ticker first
        t = yf.Ticker(sym, session=http())
        info = t.info
        if "regularMarketPrice" in info:
            return float(info["regularMarketPrice"])
        if "previousClose" in info:
            return float(info["previousClose"])
    except:
        pass

    # Fallback: fetch latest candle
    df = fetch_one(sym, "1d", "1h")
    if not df.empty:
        return float(df["close"].iloc[-1])

    return None


# ========== BREAKOUT INDICATORS (from breakout_prop_bot.py) ==========

class BreakoutIndicators:
    """GPS + Head Hunter + Oath Keeper indicators"""

    @staticmethod
    def calculate_golden_pockets(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate golden pockets (0.618-0.65 retracement)"""
        daily_high = df["high"].max()
        daily_low = df["low"].min()
        gp_data = {
            "daily_gp_high": daily_high - (daily_high - daily_low) * 0.618,
            "daily_gp_low": daily_high - (daily_high - daily_low) * 0.65,
        }
        return gp_data

    @staticmethod
    def detect_order_blocks(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Detect bullish/bearish order blocks"""
        df = df.copy()
        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]
        df["body_pct"] = df["body"] / (df["range"] + 1e-9)

        atr = df["range"].rolling(14).mean()
        vol_avg = df["volume"].rolling(20).mean()

        bullish_ob = (
            (df["close"] < df["open"]) &
            (df["body"] >= atr * 0.75) &
            (df["body_pct"] >= 0.42) &
            (df["volume"] > vol_avg * 1.2)
        )

        bearish_ob = (
            (df["close"] > df["open"]) &
            (df["body"] >= atr * 0.75) &
            (df["body_pct"] >= 0.42) &
            (df["volume"] > vol_avg * 1.2)
        )

        return bullish_ob, bearish_ob

    @staticmethod
    def detect_sweeps(df: pd.DataFrame, lookback: int = 36) -> Tuple[pd.Series, pd.Series]:
        """Detect liquidity sweeps"""
        df = df.copy()
        df["body"] = abs(df["close"] - df["open"])
        df["range"] = df["high"] - df["low"]
        df["body_pct"] = df["body"] / (df["range"] + 1e-9)
        df["wick_lower_pct"] = (df[["open", "close"]].min(axis=1) - df["low"]) / (df["range"] + 1e-9)

        atr = df["range"].rolling(14).mean()
        vol_avg = df["volume"].rolling(20).mean()

        prev_low = df["low"].rolling(lookback).min().shift(1)
        sweep_low = (
            (df["low"] < prev_low) &
            (df["close"] > prev_low) &
            (df["wick_lower_pct"] >= 0.65) &
            (df["body_pct"] <= 0.30) &
            (df["volume"] > vol_avg * 1.35)
        )

        prev_high = df["high"].rolling(lookback).max().shift(1)
        df["wick_upper_pct"] = (df["high"] - df[["open", "close"]].max(axis=1)) / (df["range"] + 1e-9)
        sweep_high = (
            (df["high"] > prev_high) &
            (df["close"] < prev_high) &
            (df["wick_upper_pct"] >= 0.65) &
            (df["body_pct"] <= 0.30) &
            (df["volume"] > vol_avg * 1.35)
        )

        return sweep_low, sweep_high

    @staticmethod
    def calculate_wt_divergence(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Wave Trend divergence"""
        n1, n2 = 10, 21
        ap = (df["high"] + df["low"]) / 2
        esa = ap.ewm(span=n1, adjust=False).mean()
        d = abs(ap - esa).ewm(span=n1, adjust=False).mean()
        ci = (ap - esa) / (0.015 * d + 1e-9)
        wt1 = ci.ewm(span=n2, adjust=False).mean()
        wt2 = wt1.rolling(4).mean()
        return wt1, wt2

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
        """Calculate VWAP and bands"""
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        vwap = (typical_price * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-9)

        variance = ((typical_price - vwap) ** 2 * df["volume"]).cumsum() / (df["volume"].cumsum() + 1e-9)
        std = np.sqrt(variance)

        return (
            vwap,
            vwap + std,
            vwap - std,
            vwap + 2 * std,
            vwap - 2 * std
        )

    @staticmethod
    def calculate_money_flow(df: pd.DataFrame, length: int = 8) -> pd.Series:
        """Money flow index"""
        up_volume = df["volume"] * (df["close"] > df["close"].shift(1)).astype(int)
        down_volume = df["volume"] * (df["close"] < df["close"].shift(1)).astype(int)

        mf_up = up_volume.rolling(length).mean()
        mf_down = down_volume.rolling(length).mean()

        money_flow = 100 * mf_up / (mf_up + mf_down + 1e-10)
        return money_flow

    @staticmethod
    def detect_macro_pivots(df: pd.DataFrame, money_flow: pd.Series, left: int = 6, right: int = 6) -> Dict:
        """Detect macro pivots for divergence analysis"""
        price_highs, price_lows = [], []
        price_high_bars, price_low_bars = [], []
        mf_highs, mf_lows = [], []
        mf_high_bars, mf_low_bars = [], []

        lookback = min(100, len(df))

        for i in range(left, lookback - right):
            # Price pivot high
            is_ph = all(df["high"].iloc[j] < df["high"].iloc[i]
                       for j in range(i - left, i + right + 1) if j != i)
            if is_ph:
                price_highs.append(df["high"].iloc[i])
                price_high_bars.append(i)

            # Price pivot low
            is_pl = all(df["low"].iloc[j] > df["low"].iloc[i]
                       for j in range(i - left, i + right + 1) if j != i)
            if is_pl:
                price_lows.append(df["low"].iloc[i])
                price_low_bars.append(i)

            # MF pivot high
            is_mfh = all(money_flow.iloc[j] < money_flow.iloc[i]
                        for j in range(i - left, i + right + 1) if j != i)
            if is_mfh:
                mf_highs.append(money_flow.iloc[i])
                mf_high_bars.append(i)

            # MF pivot low
            is_mfl = all(money_flow.iloc[j] > money_flow.iloc[i]
                        for j in range(i - left, i + right + 1) if j != i)
            if is_mfl:
                mf_lows.append(money_flow.iloc[i])
                mf_low_bars.append(i)

        return {
            "price_highs": price_highs[-2:] if len(price_highs) >= 2 else [],
            "price_lows": price_lows[-2:] if len(price_lows) >= 2 else [],
            "price_high_bars": price_high_bars[-2:] if len(price_high_bars) >= 2 else [],
            "price_low_bars": price_low_bars[-2:] if len(price_low_bars) >= 2 else [],
            "mf_highs": mf_highs[-2:] if len(mf_highs) >= 2 else [],
            "mf_lows": mf_lows[-2:] if len(mf_lows) >= 2 else [],
            "mf_high_bars": mf_high_bars[-2:] if len(mf_high_bars) >= 2 else [],
            "mf_low_bars": mf_low_bars[-2:] if len(mf_low_bars) >= 2 else [],
        }

    @staticmethod
    def detect_major_divergences(df: pd.DataFrame, money_flow: pd.Series) -> Dict:
        """Detect major divergences"""
        pivots = BreakoutIndicators.detect_macro_pivots(df, money_flow)

        reg_bull = reg_bear = hid_bull = hid_bear = False

        if len(pivots["price_lows"]) >= 2 and len(pivots["mf_lows"]) >= 2:
            reg_bull = (pivots["price_lows"][-1] < pivots["price_lows"][-2] and
                       pivots["mf_lows"][-1] > pivots["mf_lows"][-2])

        if len(pivots["price_highs"]) >= 2 and len(pivots["mf_highs"]) >= 2:
            reg_bear = (pivots["price_highs"][-1] > pivots["price_highs"][-2] and
                       pivots["mf_highs"][-1] < pivots["mf_highs"][-2])

        if len(pivots["price_lows"]) >= 2 and len(pivots["mf_lows"]) >= 2:
            hid_bull = (pivots["price_lows"][-1] > pivots["price_lows"][-2] and
                       pivots["mf_lows"][-1] < pivots["mf_lows"][-2])

        if len(pivots["price_highs"]) >= 2 and len(pivots["mf_highs"]) >= 2:
            hid_bear = (pivots["price_highs"][-1] < pivots["price_highs"][-2] and
                       pivots["mf_highs"][-1] > pivots["mf_highs"][-2])

        return {
            "reg_bull": reg_bull,
            "reg_bear": reg_bear,
            "hid_bull": hid_bull,
            "hid_bear": hid_bear,
            "has_major_div": reg_bull or reg_bear or hid_bull or hid_bear
        }


# ========== SIGNAL GENERATION ==========

def gps_signal(df: pd.DataFrame) -> Tuple[bool, bool, int]:
    """GPS master signal - lowered thresholds for more signals"""
    if len(df) < 50:  # Lowered from 100
        return False, False, 0

    gp_data = BreakoutIndicators.calculate_golden_pockets(df)
    bullish_ob, bearish_ob = BreakoutIndicators.detect_order_blocks(df)
    sweep_low, sweep_high = BreakoutIndicators.detect_sweeps(df)
    wt1, wt2 = BreakoutIndicators.calculate_wt_divergence(df)

    current_price = float(df["close"].iloc[-1])
    vol_avg = float(df["volume"].rolling(20).mean().iloc[-1])
    current_vol = float(df["volume"].iloc[-1])

    confluence = 0
    gp_threshold = 0.02

    if abs(current_price - gp_data["daily_gp_low"]) / current_price < gp_threshold:
        confluence += 20

    if current_vol > vol_avg * 1.5:
        confluence += 20

    if bullish_ob.iloc[-1]:
        confluence += 16
    if bearish_ob.iloc[-1]:
        confluence += 16

    if sweep_low.iloc[-1]:
        confluence += 18
    if sweep_high.iloc[-1]:
        confluence += 18

    wt_bull_cross = (wt1.iloc[-1] > wt2.iloc[-1]) and (wt1.iloc[-2] <= wt2.iloc[-2])
    wt_bear_cross = (wt1.iloc[-1] < wt2.iloc[-1]) and (wt1.iloc[-2] >= wt2.iloc[-2])

    if wt_bull_cross and wt1.iloc[-1] < -35:
        confluence += 20
    if wt_bear_cross and wt1.iloc[-1] > 35:
        confluence += 20

    # Lowered thresholds: confluence >= 40 (was 55), or strong volume + any pattern
    bull_signal = (
        (confluence >= 40 and (sweep_low.iloc[-1] or bullish_ob.iloc[-1])) or
        (confluence >= 30 and current_vol > vol_avg * 1.5 and (sweep_low.iloc[-1] or bullish_ob.iloc[-1])) or
        (confluence >= 50)  # High confluence alone
    ) and current_vol > vol_avg * 0.8  # Lower volume requirement

    bear_signal = (
        (confluence >= 40 and (sweep_high.iloc[-1] or bearish_ob.iloc[-1])) or
        (confluence >= 30 and current_vol > vol_avg * 1.5 and (sweep_high.iloc[-1] or bearish_ob.iloc[-1])) or
        (confluence >= 50)  # High confluence alone
    ) and current_vol > vol_avg * 0.8  # Lower volume requirement

    return bull_signal, bear_signal, confluence


def head_hunter_signal(df: pd.DataFrame) -> Tuple[bool, bool]:
    """Head Hunter VWAP signals"""
    if len(df) < 50:
        return False, False

    vwap, vwap_u1, vwap_l1, vwap_u2, vwap_l2 = BreakoutIndicators.calculate_vwap(df)

    current_price = float(df["close"].iloc[-1])
    vol_avg = float(df["volume"].rolling(14).mean().iloc[-1])

    vwap_tap_up = abs(df["low"].iloc[-1] - vwap.iloc[-1]) / (vwap.iloc[-1] + 1e-9) < 0.001
    vwap_tap_down = abs(df["high"].iloc[-1] - vwap.iloc[-1]) / (vwap.iloc[-1] + 1e-9) < 0.001

    lower1_tap = abs(df["low"].iloc[-1] - vwap_l1.iloc[-1]) / (vwap_l1.iloc[-1] + 1e-9) < 0.001
    lower2_tap = abs(df["low"].iloc[-1] - vwap_l2.iloc[-1]) / (vwap_l2.iloc[-1] + 1e-9) < 0.001

    upper1_tap = abs(df["high"].iloc[-1] - vwap_u1.iloc[-1]) / (vwap_u1.iloc[-1] + 1e-9) < 0.001
    upper2_tap = abs(df["high"].iloc[-1] - vwap_u2.iloc[-1]) / (vwap_u2.iloc[-1] + 1e-9) < 0.001

    df = df.copy()
    df["wick_lower_pct"] = (df[["open", "close"]].min(axis=1) - df["low"]) / (df["high"] - df["low"] + 1e-9)
    df["wick_upper_pct"] = (df["high"] - df[["open", "close"]].max(axis=1)) / (df["high"] - df["low"] + 1e-9)

    big_lower_wick = df["wick_lower_pct"].iloc[-1] > 0.5
    big_upper_wick = df["wick_upper_pct"].iloc[-1] > 0.5
    high_vol = df["volume"].iloc[-1] > vol_avg * 1.2

    hh_long = (
        (lower1_tap or lower2_tap or (vwap_tap_up and current_price < vwap.iloc[-1])) and
        big_lower_wick and
        high_vol and
        df["close"].iloc[-1] > df["open"].iloc[-1]
    )

    hh_short = (
        (upper1_tap or upper2_tap or (vwap_tap_down and current_price > vwap.iloc[-1])) and
        big_upper_wick and
        high_vol and
        df["close"].iloc[-1] < df["open"].iloc[-1]
    )

    return hh_long, hh_short


def oath_keeper_signal(df: pd.DataFrame) -> Tuple[bool, bool, float]:
    """Oath Keeper v2 - Major Divergences"""
    if len(df) < 60:
        return False, False, 50.0

    money_flow = BreakoutIndicators.calculate_money_flow(df)
    vol_avg = float(df["volume"].rolling(20).mean().iloc[-1])
    current_vol = float(df["volume"].iloc[-1])
    current_mf = float(money_flow.iloc[-1])
    prev_mf = float(money_flow.iloc[-2]) if len(money_flow) >= 2 else current_mf

    divs = BreakoutIndicators.detect_major_divergences(df, money_flow)

    # Liquidation detection
    atr = (df["high"] - df["low"]).rolling(14).mean().iloc[-1]
    volume_spike = current_vol > vol_avg * 1.8
    wick_size = abs(df["high"].iloc[-1] - df["low"].iloc[-1]) > atr * 1.2
    price_jump = abs(df["close"].iloc[-1] - df["close"].iloc[-2]) / (df["close"].iloc[-2] + 1e-9) > 0.008
    is_liquidation = volume_spike and wick_size and price_jump

    super_bull = (
        current_mf < 30 and
        current_mf > prev_mf and
        current_vol > vol_avg * 1.5 and
        (is_liquidation or (current_vol > vol_avg * 2))
    )

    super_bear = (
        current_mf > 70 and
        current_mf < prev_mf and
        current_vol > vol_avg * 1.5 and
        (is_liquidation or (current_vol > vol_avg * 2))
    )

    ok_long = False
    if divs["has_major_div"]:
        if divs["reg_bull"] or divs["hid_bull"]:
            ok_long = True
    elif super_bull:
        ok_long = True
    elif current_mf < 30 and current_mf > prev_mf and current_vol > vol_avg:
        ok_long = True

    ok_short = False
    if divs["has_major_div"]:
        if divs["reg_bear"] or divs["hid_bear"]:
            ok_short = True
    elif super_bear:
        ok_short = True
    elif current_mf > 70 and current_mf < prev_mf and current_vol > vol_avg:
        ok_short = True

    return ok_long, ok_short, current_mf


def generate_master_signal(df: pd.DataFrame) -> Dict:
    """Combine all 3 indicators - requires 2/3 confirmations (or 1 strong signal)"""
    if len(df) < 50:  # Lowered from 100
        return {"direction": "NONE", "grade": "F", "score": 0}

    gps_long, gps_short, confluence = gps_signal(df)
    hh_long, hh_short = head_hunter_signal(df)
    ok_long, ok_short, mf_value = oath_keeper_signal(df)

    long_confirmations = sum([gps_long, hh_long, ok_long])
    short_confirmations = sum([gps_short, hh_short, ok_short])

    # Lower threshold: 2/3 confirmations OR 1 strong signal OR high confluence alone
    master_long = long_confirmations >= 2 or (long_confirmations >= 1 and confluence >= 50) or confluence >= 60
    master_short = short_confirmations >= 2 or (short_confirmations >= 1 and confluence >= 50) or confluence >= 60

    signal_grade = "C"
    if long_confirmations == 3 or short_confirmations == 3:
        signal_grade = "A+"
    elif (long_confirmations == 2 and confluence >= 60) or (short_confirmations == 2 and confluence >= 60):
        signal_grade = "A"
    elif long_confirmations == 2 or short_confirmations == 2:
        signal_grade = "B"
    elif long_confirmations == 1 or short_confirmations == 1:
        signal_grade = "C"  # Allow C grade signals

    direction = "LONG" if master_long else ("SHORT" if master_short else "NONE")

    current_price = float(df["close"].iloc[-1])
    atr = float((df["high"] - df["low"]).rolling(14).mean().iloc[-1])

    # Calculate stop/target
    if direction == "LONG":
        recent_low = float(df["low"].iloc[-10:].min())
        stop_loss = min(recent_low - atr * 0.3, current_price - atr * 1.5)
        risk = current_price - stop_loss
        take_profit = current_price + (risk * 2.5)
    elif direction == "SHORT":
        recent_high = float(df["high"].iloc[-10:].max())
        stop_loss = max(recent_high + atr * 0.3, current_price + atr * 1.5)
        risk = stop_loss - current_price
        take_profit = current_price - (risk * 2.5)
    else:
        stop_loss = current_price
        take_profit = current_price
        risk = 0

    rr_ratio = (abs(take_profit - current_price) / (risk + 1e-9)) if risk > 0 else 0

    return {
        "direction": direction,
        "grade": signal_grade,
        "score": long_confirmations if master_long else short_confirmations,
        "confluence": confluence,
        "gps": gps_long or gps_short,
        "head_hunter": hh_long or hh_short,
        "oath_keeper": ok_long or ok_short,
        "money_flow": mf_value,
        "entry": current_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "rr_ratio": rr_ratio,
        "timestamp": df.index[-1] if hasattr(df.index[-1], 'isoformat') else now_utc().isoformat()
    }


# ========== DISCORD ==========

def post_discord(embed: Dict):
    """Send Discord embed"""
    if not WEBHOOK:
        return

    try:
        r = http().post(WEBHOOK, json={"embeds": [embed]}, timeout=15)
        if r.status_code >= 300:
            logger.error(f"Discord error: {r.status_code} {r.text[:200]}")
    except Exception as e:
        logger.error(f"Discord exception: {e}")


# ========== PAPER TRADING ==========

def load_state() -> Dict:
    try:
        return json.load(open(STATE_FILE))
    except:
        return {}


def save_state(state: Dict):
    json.dump(state, open(STATE_FILE, "w"), indent=2)


class PaperTrading:
    """Paper trading account"""

    def __init__(self):
        self.state = load_state()
        if "balance" not in self.state:
            self.state["balance"] = ACCOUNT_SIZE
        if "trades" not in self.state:
            self.state["trades"] = []
        if "history" not in self.state:
            self.state["history"] = []
        if "stats" not in self.state:
            self.state["stats"] = {
                "wins": 0, "losses": 0, "realized_pnl": 0.0,
                "unrealized_pnl": 0.0, "total_pnl": 0.0
            }

    def open_trade(self, signal: Dict, symbol: str) -> Optional[Dict]:
        """Open a paper trade"""
        balance = float(self.state["balance"])
        risk_amount = balance * RISK_PER_TRADE

        entry = signal["entry"]
        stop = signal["stop_loss"]
        price_risk = abs(entry - stop)

        if price_risk == 0:
            return None

        # Calculate position size
        qty = risk_amount / price_risk

        trade = {
            "id": f"TM_{int(time.time())}_{symbol}",
            "symbol": symbol,
            "direction": signal["direction"],
            "entry": entry,
            "stop": stop,
            "tp": signal["take_profit"],
            "qty": qty,
            "opened": now_utc().isoformat(),
            "grade": signal["grade"],
            "status": "OPEN"
        }

        self.state["trades"].append(trade)
        save_state(self.state)
        logger.info(f"Paper trade opened: {trade['id']}")
        return trade

    def monitor_positions(self):
        """Monitor open positions - only during market hours"""
        if not self.state.get("trades"):
            return

        updated_trades = []
        closed_trades = []

        for trade in self.state["trades"][:]:
            if trade["status"] != "OPEN":
                continue

            symbol = trade["symbol"]

            # Only monitor/close positions when market is open
            if not is_market_open(symbol):
                updated_trades.append(trade)  # Keep position but don't check TP/SL
                continue

            current_price = fetch_realtime_price(symbol)
            if not current_price:
                updated_trades.append(trade)
                continue

            direction = trade["direction"]
            entry = trade["entry"]
            stop = trade["stop"]
            tp = trade["tp"]
            qty = trade["qty"]

            side = 1 if direction == "LONG" else -1
            pnl = (current_price - entry) * side * qty

            hit_reason = None
            if direction == "LONG":
                if current_price >= tp:
                    hit_reason = "TAKE_PROFIT"
                elif current_price <= stop:
                    hit_reason = "STOP_LOSS"
            else:  # SHORT
                if current_price <= tp:
                    hit_reason = "TAKE_PROFIT"
                elif current_price >= stop:
                    hit_reason = "STOP_LOSS"

            if hit_reason:
                # Close position
                balance = float(self.state["balance"])
                balance += pnl

                stats = self.state["stats"]
                stats["realized_pnl"] += pnl
                stats["total_pnl"] = stats["realized_pnl"] + stats.get("unrealized_pnl", 0)

                if pnl > 0:
                    stats["wins"] += 1
                else:
                    stats["losses"] += 1

                closed_trade = {
                    **trade,
                    "exit": current_price,
                    "exit_time": now_utc().isoformat(),
                    "pnl": pnl,
                    "pnl_pct": (pnl / (entry * qty)) * 100 if entry * qty > 0 else 0,
                    "reason": hit_reason,
                    "status": "CLOSED"
                }

                self.state["history"].append(closed_trade)
                closed_trades.append(closed_trade)

                # Discord alert
                if WEBHOOK:
                    color = COLOR_GREEN if pnl > 0 else COLOR_RED
                    emoji = "🎉" if pnl > 0 else "🛑"
                    embed = {
                        "title": f"{emoji} Position Closed: {symbol} {direction}",
                        "color": color,
                        "timestamp": now_utc().isoformat(),
                        "fields": [
                            {"name": "Reason", "value": hit_reason.replace("_", " "), "inline": True},
                            {"name": "Entry", "value": f"${entry:.3f}", "inline": True},
                            {"name": "Exit", "value": f"${current_price:.3f}", "inline": True},
                            {"name": "PnL", "value": f"${pnl:+.2f}", "inline": True},
                            {"name": "Balance", "value": f"${balance:.2f}", "inline": True},
                        ]
                    }
                    post_discord(embed)
            else:
                trade["unrealized_pnl"] = pnl
                updated_trades.append(trade)

        # Update state
        stats = self.state["stats"]
        stats["unrealized_pnl"] = sum(t.get("unrealized_pnl", 0) for t in updated_trades)

        self.state["trades"] = updated_trades
        self.state["balance"] = float(self.state["balance"]) + sum(ct["pnl"] for ct in closed_trades)
        save_state(self.state)

        return closed_trades


# ========== MAIN SCANNER ==========

def scan_markets(symbols: List[str], category: str, timeframe: str = "1h", period: str = "59d") -> List[Dict]:
    """Scan symbols and return signals

    Args:
        symbols: List of symbols to scan
        category: Category name (STOCK, FUTURES, FOREX)
        timeframe: Data timeframe ("1h" for intraday, "1d" for weekly)
        period: Data period to fetch
    """
    signals = []

    for sym in symbols:
        try:
            df = fetch_one(sym, period, timeframe)
            if df.empty or len(df) < 50:  # Lowered from 100 to match signal generation
                if df.empty:
                    logger.debug(f"No data for {sym}")
                else:
                    logger.debug(f"Insufficient data for {sym}: {len(df)} rows (need 50)")
                continue

            signal = generate_master_signal(df)
            if signal["direction"] == "NONE":
                # Fallback: Create a basic signal if we have any confluence
                if signal.get("confluence", 0) >= 20:
                    # Create a basic directional signal based on price action
                    current_price = float(df["close"].iloc[-1])
                    ema_21 = df["close"].ewm(span=21, adjust=False).mean().iloc[-1]
                    direction = "LONG" if current_price > ema_21 else "SHORT"
                    atr = float((df["high"] - df["low"]).rolling(14).mean().iloc[-1])

                    if direction == "LONG":
                        stop_loss = current_price - atr * 1.5
                        take_profit = current_price + atr * 2.5
                    else:
                        stop_loss = current_price + atr * 1.5
                        take_profit = current_price - atr * 2.5

                    risk = abs(current_price - stop_loss)
                    reward = abs(take_profit - current_price)
                    rr_ratio = reward / risk if risk > 0 else 0

                    signal = {
                        "direction": direction,
                        "grade": "C",
                        "score": 1,
                        "confluence": signal.get("confluence", 20),
                        "gps": False,
                        "head_hunter": False,
                        "oath_keeper": False,
                        "money_flow": 50.0,
                        "entry": current_price,
                        "stop_loss": stop_loss,
                        "take_profit": take_profit,
                        "rr_ratio": rr_ratio,
                        "timestamp": df.index[-1] if hasattr(df.index[-1], 'isoformat') else now_utc().isoformat()
                    }
                    logger.info(f"Fallback signal: {sym} {direction} (confluence={signal['confluence']})")
                else:
                    logger.debug(f"No signal for {sym}: grade={signal['grade']}, score={signal['score']}, conf={signal.get('confluence', 0)}")
                    continue
            else:
                logger.info(f"Signal found: {sym} {signal['direction']} {signal['grade']} (score={signal['score']}, conf={signal['confluence']})")

            signal["symbol"] = sym
            signal["category"] = category
            signal["timeframe"] = timeframe
            signals.append(signal)

            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            logger.error(f"Error scanning {sym}: {e}")
            continue

    # Sort by score
    signals.sort(key=lambda x: (x["score"], x["confluence"]), reverse=True)
    return signals


def run_weekly_analysis():
    """Run weekly analysis on Sunday - generates picks for the upcoming week"""
    logger.info("📅 Running weekly analysis for upcoming week...")

    # Scan with daily timeframe for weekly picks
    stock_signals = scan_markets(STOCKS, "STOCK", timeframe="1d", period="6mo")
    futures_signals = scan_markets(FUTURES, "FUTURES", timeframe="1d", period="6mo")
    forex_signals = scan_markets(FOREX, "FOREX", timeframe="1d", period="6mo")

    # Top weekly picks
    weekly_stocks = stock_signals[:1] if stock_signals else []
    weekly_futures = futures_signals[:1] if futures_signals else []
    weekly_forex = forex_signals[:1] if forex_signals else []

    # Save weekly picks to state
    state = load_state()
    week_start = get_week_start()
    week_key = week_start.strftime("%Y-%m-%d")

    state["weekly_picks"] = {
        "week_start": week_key,
        "generated": now_utc().isoformat(),
        "stocks": weekly_stocks[0] if weekly_stocks else None,
        "futures": weekly_futures[0] if weekly_futures else None,
        "forex": weekly_forex[0] if weekly_forex else None,
    }
    save_state(state)

    # Post weekly picks embed
    embeds = []

    if weekly_stocks or weekly_futures or weekly_forex:
        lines = []
        lines.append(f"**Week Starting:** {week_start.strftime('%B %d, %Y')}")
        lines.append("")
        lines.append("### 🎯 Weekly Picks (Swing Trades)")
        lines.append("")

        if weekly_stocks:
            s = weekly_stocks[0]
            dot = "🟢" if s["direction"] == "LONG" else "🔴"
            lines.append(
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: ${s['entry']:.2f} | Stop: ${s['stop_loss']:.2f} | TP: ${s['take_profit']:.2f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            )
            lines.append("")

        if weekly_futures:
            s = weekly_futures[0]
            dot = "🟢" if s["direction"] == "LONG" else "🔴"
            lines.append(
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: ${s['entry']:.2f} | Stop: ${s['stop_loss']:.2f} | TP: ${s['take_profit']:.2f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            )
            lines.append("")

        if weekly_forex:
            s = weekly_forex[0]
            dot = "🟢" if s["direction"] == "LONG" else "🔴"
            lines.append(
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: {s['entry']:.5f} | Stop: {s['stop_loss']:.5f} | TP: {s['take_profit']:.5f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            )

        embeds.append({
            "title": "📅 Weekly Picks for Upcoming Week",
            "description": "\n".join(lines),
            "color": COLOR_BLUE,
            "timestamp": now_utc().isoformat(),
            "footer": {"text": "Weekly swing trades - Daily timeframe analysis"}
        })

    # Add news headlines - only fresh news with links
    news = pull_news(6, max_age_hours=12)  # Only news from last 12 hours
    if news:
        news_lines = []
        for tag, headline, _, link in news:
            if link:
                news_lines.append(f"**[{tag}]** [{headline}]({link})")
            else:
                news_lines.append(f"**[{tag}]** {headline}")
        embeds.append({
            "title": "📰 Market Headlines",
            "description": "\n".join(news_lines),
            "color": COLOR_RED,
            "timestamp": now_utc().isoformat()
        })

    if WEBHOOK and embeds:
        try:
            http().post(WEBHOOK, json={"embeds": embeds}, timeout=15)
            logger.info("✅ Posted weekly picks to Discord")
        except Exception as e:
            logger.error(f"Discord error: {e}")


def run_scan():
    """Run one scan and post to Discord"""
    # Check if it's Saturday - go silent
    if is_saturday():
        logger.info("🔇 Saturday - Bot is silent (no scans)")
        return

    # Check if it's Sunday - run weekly analysis first
    if is_sunday():
        # Check if we've already generated picks for this week
        state = load_state()
        week_start = get_week_start()
        week_key = week_start.strftime("%Y-%m-%d")

        weekly_picks = state.get("weekly_picks", {})
        if weekly_picks.get("week_start") != week_key:
            logger.info("📅 Sunday detected - Generating weekly picks...")
            run_weekly_analysis()

    logger.info("🔍 Starting market scan...")

    paper = PaperTrading()
    paper.monitor_positions()

    # Scan all categories (intraday timeframe)
    stock_signals = scan_markets(STOCKS, "STOCK", timeframe="1h", period="59d")
    futures_signals = scan_markets(FUTURES, "FUTURES", timeframe="1h", period="59d")
    forex_signals = scan_markets(FOREX, "FOREX", timeframe="1h", period="59d")

    # Top picks - always show best available even if lower grade
    top_stocks = stock_signals[:3] if stock_signals else []
    top_futures = futures_signals[:1] if futures_signals else []
    top_forex = forex_signals[:1] if forex_signals else []

    # Post embeds
    embeds = []

    # Log what we found
    logger.info(f"Signals found: Stocks={len(stock_signals)}, Futures={len(futures_signals)}, Forex={len(forex_signals)}")

    # Stocks - post even if only 1-2 found
    if top_stocks:
        lines = []
        for s in top_stocks:
            dot = "🟢" if s["direction"] == "LONG" else "🔴"
            lines.append(
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: ${s['entry']:.2f} | Stop: ${s['stop_loss']:.2f} | TP: ${s['take_profit']:.2f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            )
        embeds.append({
            "title": "Stocks — Top 3 Breakout Signals",
            "description": "\n\n".join(lines),
            "color": COLOR_WHITE,
            "timestamp": now_utc().isoformat()
        })

        # Open paper trade for best stock (only if market is open)
        if top_stocks[0] and top_stocks[0]["grade"] in ["A+", "A", "B", "C"]:
            symbol = top_stocks[0]["symbol"]
            if is_market_open(symbol):
                trade = paper.open_trade(top_stocks[0], symbol)
                if trade:
                    logger.info(f"✅ Paper trade opened: {trade['id']} - {symbol} {top_stocks[0]['direction']}")
                else:
                    logger.warning(f"⚠️ Failed to open paper trade for {symbol}")
            else:
                logger.info(f"⏸️ Market closed for {symbol} - skipping paper trade")

    # Also open trades for futures and forex if found (only if market is open)
    if top_futures and top_futures[0]["grade"] in ["A+", "A", "B", "C"]:
        symbol = top_futures[0]["symbol"]
        if is_market_open(symbol):
            trade = paper.open_trade(top_futures[0], symbol)
            if trade:
                logger.info(f"✅ Paper trade opened: {trade['id']} - {symbol} {top_futures[0]['direction']}")
            else:
                logger.warning(f"⚠️ Failed to open paper trade for {symbol}")
        else:
            logger.info(f"⏸️ Market closed for {symbol} - skipping paper trade")

    if top_forex and top_forex[0]["grade"] in ["A+", "A", "B", "C"]:
        symbol = top_forex[0]["symbol"]
        if is_market_open(symbol):
            trade = paper.open_trade(top_forex[0], symbol)
            if trade:
                logger.info(f"✅ Paper trade opened: {trade['id']} - {symbol} {top_forex[0]['direction']}")
            else:
                logger.warning(f"⚠️ Failed to open paper trade for {symbol}")
        else:
            logger.info(f"⏸️ Market closed for {symbol} - skipping paper trade")

    # Futures
    if top_futures:
        s = top_futures[0]
        dot = "🟢" if s["direction"] == "LONG" else "🔴"
        embeds.append({
            "title": "Futures — Daily Breakout Pick",
            "description": (
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: ${s['entry']:.2f} | Stop: ${s['stop_loss']:.2f} | TP: ${s['take_profit']:.2f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            ),
            "color": COLOR_BLUE,
            "timestamp": now_utc().isoformat()
        })

    # Forex
    if top_forex:
        s = top_forex[0]
        dot = "🟢" if s["direction"] == "LONG" else "🔴"
        embeds.append({
            "title": "Forex — Daily Breakout Pick",
            "description": (
                f"{dot} **{s['symbol']}** {s['direction']} • {s['grade']}\n"
                f"Entry: {s['entry']:.5f} | Stop: {s['stop_loss']:.5f} | TP: {s['take_profit']:.5f}\n"
                f"R:R {s['rr_ratio']:.2f}:1 • Confluence: {s['confluence']}/100\n"
                f"[Chart]({tv_link(s['symbol'])})"
            ),
            "color": COLOR_ORANGE,
            "timestamp": now_utc().isoformat()
        })

    # Add weekly picks reminder on Sunday
    if is_sunday():
        state = load_state()
        weekly_picks = state.get("weekly_picks", {})
        if weekly_picks.get("stocks") or weekly_picks.get("futures") or weekly_picks.get("forex"):
            lines = ["**Check weekly picks above for swing trade opportunities!**"]
            if weekly_picks.get("stocks"):
                s = weekly_picks["stocks"]
                lines.append(f"📈 Weekly Stock: {s['symbol']} {s['direction']}")
            if weekly_picks.get("futures"):
                s = weekly_picks["futures"]
                lines.append(f"📊 Weekly Futures: {s['symbol']} {s['direction']}")
            if weekly_picks.get("forex"):
                s = weekly_picks["forex"]
                lines.append(f"💱 Weekly Forex: {s['symbol']} {s['direction']}")

            embeds.append({
                "title": "📅 Weekly Picks Reference",
                "description": "\n".join(lines),
                "color": COLOR_BLUE,
                "timestamp": now_utc().isoformat()
            })

    # Status
    stats = paper.state["stats"]
    balance = paper.state["balance"]
    embeds.append({
        "title": "Paper Trading Status",
        "fields": [
            {"name": "Balance", "value": f"${balance:.2f}", "inline": True},
            {"name": "Open Positions", "value": str(len([t for t in paper.state["trades"] if t["status"] == "OPEN"])), "inline": True},
            {"name": "Wins/Losses", "value": f"{stats['wins']}/{stats['losses']}", "inline": True},
            {"name": "Realized PnL", "value": f"${stats['realized_pnl']:+.2f}", "inline": True},
            {"name": "Unrealized PnL", "value": f"${stats['unrealized_pnl']:+.2f}", "inline": True},
        ],
        "color": COLOR_GREEN,
        "timestamp": now_utc().isoformat()
    })

    # Add news headlines to regular scans - only fresh news with links
    news = pull_news(6, max_age_hours=12)  # Only news from last 12 hours
    if news:
        news_lines = []
        for tag, headline, _, link in news:
            if link:
                news_lines.append(f"**[{tag}]** [{headline}]({link})")
            else:
                news_lines.append(f"**[{tag}]** {headline}")
        embeds.append({
            "title": "📰 Market Headlines",
            "description": "\n".join(news_lines),
            "color": COLOR_RED,
            "timestamp": now_utc().isoformat()
        })

    # Post all embeds
    if WEBHOOK and embeds:
        try:
            http().post(WEBHOOK, json={"embeds": embeds}, timeout=15)
            logger.info(f"✅ Posted {len(embeds)} embeds to Discord")
        except Exception as e:
            logger.error(f"Discord error: {e}")

    logger.info("✅ Scan complete")


def get_next_scan_time_et():
    """Get next scan time in ET timezone (pre-NY open ~8:30 AM or 11:00 AM)"""
    et = pytz.timezone('America/New_York')
    now_et = datetime.now(et)

    # Define scan times in ET
    scan_times = [
        now_et.replace(hour=8, minute=30, second=0, microsecond=0),  # Pre-NY open
        now_et.replace(hour=11, minute=0, second=0, microsecond=0),   # Before lunch/post-session
    ]

    # If it's Saturday or Sunday, skip
    if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
        # Next Monday 8:30 AM
        days_ahead = 7 - now_et.weekday()  # Days until Monday
        next_monday = now_et + timedelta(days=days_ahead)
        return next_monday.replace(hour=8, minute=30, second=0, microsecond=0)

    # Find next scan time today
    for scan_time in scan_times:
        if scan_time > now_et:
            return scan_time

    # If both times passed today, use first time tomorrow
    tomorrow = now_et + timedelta(days=1)
    if tomorrow.weekday() >= 5:  # If tomorrow is weekend, go to Monday
        days_ahead = 7 - tomorrow.weekday()
        tomorrow = tomorrow + timedelta(days=days_ahead)
    return tomorrow.replace(hour=8, minute=30, second=0, microsecond=0)


def main_loop():
    """Main scanning loop - scans twice daily: pre-NY open (8:30 AM ET) and 11:00 AM ET"""
    logger.info("🚀 Market Pulse Bot started")
    logger.info("⏰ Scan Schedule: Twice daily")
    logger.info("   - Pre-NY Open: 8:30 AM ET")
    logger.info("   - Post-Session: 11:00 AM ET")
    logger.info("🔇 Saturday: Silent (no scans)")
    logger.info("📅 Sunday: Weekly picks generated")

    # Post startup notification
    if WEBHOOK:
        embed = {
            "title": "🤖 Market Pulse Bot Activated",
            "description": (
                "**Scan Schedule:** Twice daily\n"
                "• Pre-NY Open: 8:30 AM ET\n"
                "• Post-Session: 11:00 AM ET\n\n"
                "**Schedule:**\n"
                "- Monday-Friday: 2 scans per day\n"
                "- Saturday: Silent (no scans)\n"
                "- Sunday: Weekly picks generated\n\n"
                "Bot is now running and will scan markets automatically."
            ),
            "color": COLOR_GREEN,
            "timestamp": now_utc().isoformat()
        }
        try:
            http().post(WEBHOOK, json={"embeds": [embed]}, timeout=15)
        except:
            pass

    # Run initial scan if it's a scan time
    et = pytz.timezone('America/New_York')
    now_et = datetime.now(et)
    if now_et.weekday() < 5:  # Monday-Friday
        current_hour = now_et.hour
        current_min = now_et.minute
        # If between 8:00-9:00 or 10:30-11:30, run scan
        if (8 <= current_hour < 9) or (current_hour == 11 and current_min < 30):
            logger.info("🕐 Initial scan time detected - running scan now")
            run_scan()

    while True:
        try:
            # Check if Saturday - skip scan but keep monitoring
            if is_saturday():
                logger.info("🔇 Saturday - Silent mode, skipping scan")
                # Sleep until Sunday
                time.sleep(3600)  # Check every hour
                continue

            # Get next scan time
            et = pytz.timezone('America/New_York')
            next_scan = get_next_scan_time_et()
            now_et = datetime.now(et)

            # Calculate seconds until next scan
            wait_seconds = (next_scan - now_et).total_seconds()

            if wait_seconds < 0:
                # Should have scanned already, run now
                run_scan()
                wait_seconds = 3600  # Wait 1 hour before recalculating

            wait_hours = wait_seconds / 3600
            logger.info(f"⏰ Next scan: {next_scan.strftime('%Y-%m-%d %H:%M %Z')} (in {wait_hours:.1f} hours)")

            # Sleep in smaller chunks to check for scan time
            sleep_chunk = min(300, wait_seconds)  # Check every 5 min or less
            time.sleep(sleep_chunk)

            # Check if it's time to scan
            now_et = datetime.now(et)
            if now_et.weekday() < 5:  # Monday-Friday
                current_hour = now_et.hour
                current_min = now_et.minute
                # Check if we're at scan time (8:30 or 11:00)
                if (current_hour == 8 and current_min >= 30) or (current_hour == 11 and current_min == 0):
                    logger.info(f"🕐 Scan time reached: {now_et.strftime('%H:%M %Z')}")
                    run_scan()
                    # Sleep a bit to avoid double-scanning
                    time.sleep(120)  # 2 minutes

        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scan loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(300)  # Wait 5 min on error


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            run_scan()
        elif sys.argv[1] == "weekly":
            run_weekly_analysis()
        else:
            print("Usage: python traditional_markets_bot.py [once|weekly]")
            print("  once    - Run one scan")
            print("  weekly  - Generate weekly picks")
            print("  (none)  - Run continuous loop")
    else:
        main_loop()
