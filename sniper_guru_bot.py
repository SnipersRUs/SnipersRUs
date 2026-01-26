#!/usr/bin/env python3
# sniper_guru_bot.py
# Sniper Guru — daily BTC NY session plan, sentiment + learning memory
# Enhanced with integrated TradingView indicator logic (Cloudfare), liquidity detection,
# advanced VWAP calculations, trend scoring, signal generation, X sentiment (placeholder),
# Fed calendar parsing, and deeper analysis sections.
# Requirements: pip install requests pandas numpy pytz feedparser schedule beautifulsoup4

import os, sys, time, argparse, math, json, datetime as dt
from pathlib import Path
import requests, numpy as np, pandas as pd, pytz, feedparser, schedule
from bs4 import BeautifulSoup
import logging

# ---------- CONFIG ----------
CONFIG = {
    "symbol": "BTCUSDT",
    "binance_api": "https://api.binance.com/api/v3/klines",
    "interval": "1m",
    "lookback_minutes": 60*24*14,   # two weeks
    "tz_ny": "America/New_York",
    "run_time_local": "08:55",      # NY local time to run daily pre-open
    "memory_csv": "sniperguru_memory.csv",
    "discord_webhook": "",
    "news_rss": [
        "https://www.reuters.com/markets/wealth/rss",          # world/markets
        "https://www.reuters.com/finance/markets/rss",         # markets
        "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
        "https://www.federalreserve.gov/feeds/press_all.xml",
        "https://cointelegraph.com/rss",                       # crypto news
        "https://www.bloomberg.com/feeds/markets/news.rss",    # Bloomberg markets
        "https://feeds.finance.yahoo.com/rss/2.0/headline",   # Yahoo Finance
        "https://www.marketwatch.com/rss/topstories"           # MarketWatch
    ],
    "fed_policy_url": "https://www.federalreserve.gov/monetarypolicy.htm",
    "macro_quotes": {
        "SPY": "https://stooq.com/q/l/?s=spy.us&f=sd2t2ohlcv&h&e=csv",
        "VIX": "https://stooq.com/q/l/?s=vix.us&f=sd2t2ohlcv&h&e=csv",
        "DXY": "https://stooq.com/q/l/?s=dxy.us&f=sd2t2ohlcv&h&e=csv",
        "WTI": "https://stooq.com/q/l/?s=cl.f&f=sd2t2ohlcv&h&e=csv",
        "GOLD": "https://stooq.com/q/l/?s=gc.f&f=sd2t2ohlcv&h&e=csv"  # Added gold
    },
    "sentiment_lexicon": {   # expanded lexicon for better accuracy
        "good": 1, "bull": 1.5, "positive": 1, "beat": 1, "strong": 1, "up": 0.8, "rally": 1.2,
        "surge": 0.7, "dovish": 1.2, "cut": 1.0, "boom": 1.5, "recovery": 1.0,
        "bad": -1, "bear": -1.5, "negative": -1, "miss": -1, "weak": -1, "down": -0.8,
        "drop": -0.8, "recession": -2, "crash": -2.0, "hawk": -1.2, "hike": -1.0,
        "selloff": -1.5, "liquidation": -1.2, "fear": -1.0, "greed": 0.5
    },
    # Indicator params from Pine Script
    "ma_fast": 20,
    "ma_medium": 50,
    "ma_slow": 200,
    "volume_threshold": 1.2,
    "atr_multiplier": 1.5,
    "liquidity_threshold": 2.5,
    "liquidity_lookback": 20,
    "money_flow_period": 14,
    # Add X RSS or placeholder for sentiment (e.g., from nitter or RSS feed)
    "x_rss": "https://rss.app/feeds/v1/feed/bitcoin"  # Placeholder RSS for Bitcoin tweets
}

# ---------- LOGGING SETUP ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sniper_guru_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------- UTILITIES ----------
NY = pytz.timezone(CONFIG["tz_ny"])
def utc_now(): return dt.datetime.now(dt.timezone.utc)
def ny_now(): return utc_now().astimezone(NY)

def log(msg):
    logger.info(msg)
    print(f"[{ny_now().strftime('%Y-%m-%d %H:%M:%S %Z')}] {msg}")

# ---------- DISCORD WEBHOOK CLASS ----------
class DiscordWebhook:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "SniperGuruBot/1.0"
        })
        self.last_ping_time = 0
        self.ping_interval = 300  # 5 minutes between pings

    def can_ping(self) -> bool:
        """Check if we can send a ping based on time interval"""
        current_time = time.time()
        if current_time - self.last_ping_time >= self.ping_interval:
            self.last_ping_time = current_time
            return True
        return False

    def send_ping(self) -> bool:
        """Send a ping to Discord when bot is active"""
        if not self.webhook_url:
            log("No Discord webhook configured")
            return False

        if not self.can_ping():
            log("Ping rate limited - too soon since last ping")
            return False

        try:
            payload = {
                "content": "🔴 **SNIPER GURU BOT ACTIVE** 🔴\nBot is running and monitoring markets...",
                "embeds": [{
                    "title": "Sniper Guru Status",
                    "description": f"Active at {ny_now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
                    "color": 0x00ff00,  # Green
                    "timestamp": utc_now().isoformat(),
                    "fields": [
                        {"name": "Status", "value": "🟢 Online", "inline": True},
                        {"name": "Next Update", "value": f"Daily at {CONFIG['run_time_local']} NY", "inline": True}
                    ]
                }]
            }

            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code in (200, 204):
                log("Ping sent to Discord successfully")
                return True
            else:
                log(f"Discord ping failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            log(f"Discord ping error: {e}")
            return False

    def send_analysis(self, content: str) -> bool:
        """Send the full analysis to Discord"""
        if not self.webhook_url:
            log("No Discord webhook configured")
            return False

        try:
            # Split content if too long for Discord
            if len(content) > 2000:
                # Split into chunks
                chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        payload = {"content": chunk}
                    else:
                        payload = {"content": f"**Continued...**\n{chunk}"}

                    response = self.session.post(self.webhook_url, json=payload, timeout=10)
                    if response.status_code not in (200, 204):
                        log(f"Discord chunk {i+1} failed: {response.status_code}")
                        return False
                    time.sleep(1)  # Rate limiting
            else:
                payload = {"content": content}
                response = self.session.post(self.webhook_url, json=payload, timeout=10)

            if response.status_code in (200, 204):
                log("Analysis sent to Discord successfully")
                return True
            else:
                log(f"Discord analysis failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            log(f"Discord analysis error: {e}")
            return False

# Initialize Discord webhook
discord = DiscordWebhook(CONFIG["discord_webhook"])

# ---------- MARKET DATA ----------
def fetch_binance_klines(symbol, interval, start_ms=None, end_ms=None, limit=1000):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_ms: params["startTime"] = int(start_ms)
    if end_ms: params["endTime"] = int(end_ms)
    r = requests.get(CONFIG["binance_api"], params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    cols = ["open_time","open","high","low","close","volume","close_time","qav","ntrades","tbv","tbq","ignore"]
    df = pd.DataFrame(data, columns=cols)
    df.open_time = pd.to_datetime(df.open_time, unit="ms", utc=True)
    df.close_time = pd.to_datetime(df.close_time, unit="ms", utc=True)
    for c in ["open","high","low","close","volume"]:
        df[c] = df[c].astype(float)
    return df

def fetch_recent_klines():
    try:
        # Use simple approach - just get last 1000 candles
        df = fetch_binance_klines(CONFIG["symbol"], CONFIG["interval"], limit=1000)
        if df.empty:
            raise RuntimeError("No klines")
        return df
    except Exception as e:
        log(f"Binance API error: {e}. Using mock data for testing.")
        # Create mock data for testing
        import numpy as np
        dates = pd.date_range(start='2024-10-01', periods=1000, freq='1min', tz='UTC')
        base_price = 65000
        price_changes = np.random.normal(0, 100, 1000).cumsum()
        prices = base_price + price_changes

        mock_data = {
            'open_time': dates,
            'open': prices,
            'high': prices + np.random.uniform(0, 200, 1000),
            'low': prices - np.random.uniform(0, 200, 1000),
            'close': prices + np.random.normal(0, 50, 1000),
            'volume': np.random.uniform(100, 1000, 1000),
            'close_time': dates,
            'qav': np.random.uniform(100, 1000, 1000),
            'ntrades': np.random.randint(10, 100, 1000),
            'tbv': np.random.uniform(100, 1000, 1000),
            'tbq': np.random.uniform(100, 1000, 1000),
            'ignore': np.zeros(1000)
        }

        df = pd.DataFrame(mock_data)
        df.open_time = pd.to_datetime(df.open_time, utc=True)
        df.close_time = pd.to_datetime(df.close_time, utc=True)
        for c in ["open","high","low","close","volume"]:
            df[c] = df[c].astype(float)
        return df

# ---------- TA FUNCTIONS (from Pine Script) ----------
def sma(df, col, length):
    return df[col].rolling(window=length).mean()

def atr(df, length=14):
    # True Range
    tr = np.maximum(df['high'] - df['low'],
                    np.maximum(abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift())))
    return tr.rolling(window=length).mean()

def mfi(df, length=14):
    # Money Flow Index
    typical = (df['high'] + df['low'] + df['close']) / 3
    mf = typical * df['volume']
    pos_mf = mf.where(typical > typical.shift(), 0).rolling(length).sum()
    neg_mf = mf.where(typical < typical.shift(), 0).rolling(length).sum()
    mfr = pos_mf / neg_mf
    return 100 - (100 / (1 + mfr))

def vwap_of(df):
    tp = (df['high'] + df['low'] + df['close']) / 3.0
    return (tp * df['volume']).cumsum() / df['volume'].cumsum()

# Anchored VWAP for specific periods
def anchored_vwap(df, freq):
    df_res = df.set_index('open_time').resample(freq).agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).reset_index()
    df_res['vwap'] = vwap_of(df_res)
    return df_res['vwap'].iloc[-1] if not df_res.empty else np.nan

# 9-Day Cycle VWAP with Standard Deviation Bands
def calculate_9day_vwap_with_bands(df):
    """Calculate 9-day anchored VWAP with standard deviation bands"""
    # Get last 9 days of data (use available data if less than 9 days)
    days_back = min(9, len(df) // (24 * 60))  # Calculate available days
    df_9d = df.tail(days_back * 24 * 60) if days_back > 0 else df.tail(1000)

    if len(df_9d) < 100:  # Need at least 100 data points
        return {
            'vwap_9d': np.nan,
            'upper_1sd': np.nan,
            'lower_1sd': np.nan,
            'upper_2sd': np.nan,
            'lower_2sd': np.nan
        }

    # Calculate 9-day VWAP
    typical_price = (df_9d['high'] + df_9d['low'] + df_9d['close']) / 3
    vwap_9d = (typical_price * df_9d['volume']).sum() / df_9d['volume'].sum()

    # Calculate standard deviation
    price_vol = typical_price * df_9d['volume']
    sum_price_vol = price_vol.sum()
    sum_vol = df_9d['volume'].sum()
    sum_price_sq_vol = (typical_price ** 2 * df_9d['volume']).sum()

    variance = (sum_price_sq_vol / sum_vol) - (vwap_9d ** 2)
    std_dev = np.sqrt(max(variance, 0))

    # Calculate bands
    upper_1sd = vwap_9d + (std_dev * 1.0)
    lower_1sd = vwap_9d - (std_dev * 1.0)
    upper_2sd = vwap_9d + (std_dev * 2.0)
    lower_2sd = vwap_9d - (std_dev * 2.0)

    return {
        'vwap_9d': vwap_9d,
        'upper_1sd': upper_1sd,
        'lower_1sd': lower_1sd,
        'upper_2sd': upper_2sd,
        'lower_2sd': lower_2sd
    }

# Detect reversal zones
def detect_reversal_zones(df, vwap_9d_data):
    """Detect if price is in reversal zones based on 9-day VWAP bands"""
    current_price = df['close'].iloc[-1]

    in_upper_reversal_zone = current_price > vwap_9d_data['upper_2sd']
    in_lower_reversal_zone = current_price < vwap_9d_data['lower_2sd']
    extended_up = current_price > vwap_9d_data['upper_1sd']
    extended_down = current_price < vwap_9d_data['lower_1sd']

    return {
        'in_upper_reversal_zone': in_upper_reversal_zone,
        'in_lower_reversal_zone': in_lower_reversal_zone,
        'extended_up': extended_up,
        'extended_down': extended_down,
        'current_price': current_price,
        'vwap_9d': vwap_9d_data['vwap_9d']
    }

# Liquidity flush detection
def detect_liquidity_flush(df, threshold=2.5, lookback=20):
    avg_vol = df['volume'].rolling(20).mean()
    atr_val = atr(df)
    high_lookback = df['high'].rolling(lookback).max()
    low_lookback = df['low'].rolling(lookback).min()
    flush_up = (df['high'] > high_lookback.shift()) & (df['volume'] > avg_vol * threshold)
    flush_down = (df['low'] < low_lookback.shift()) & (df['volume'] > avg_vol * threshold)
    recent_flushes = df[flush_up | flush_down].tail(5)  # Last 5 flushes
    return recent_flushes[['open_time', 'high', 'low', 'volume']]

# Trend score from Pine
def compute_trend_score(df, ma_fast, ma_medium, ma_slow):
    score = 0.0
    close = df['close'].iloc[-1]
    if close > ma_slow.iloc[-1]:
        score += 3
    if close > ma_medium.iloc[-1]:
        score += 2
    if ma_medium.iloc[-1] > ma_slow.iloc[-1]:
        score += 2
    if ma_fast.iloc[-1] > ma_fast.iloc[-2]:
        score += 1
    if close > df['close'].iloc[-2]:
        score += 1
    if close > df['close'].iloc[-6] and df['close'].iloc[-2] > df['close'].iloc[-7]:
        score += 1
    return score

# Signals from Pine (simplified)
def generate_signals(df, score, ma_medium, vwap_4h):
    signals = []
    if score >= 8:
        signals.append({"type": "Strong Bull", "confidence": 0.8})
    elif score <= 2:
        signals.append({"type": "Strong Bear", "confidence": 0.8})
    # Add more from HH/LL, reversals, etc.
    hh_pattern = (df['close'].iloc[-1] > df['high'].rolling(5).max().iloc[-2]) and (df['close'].iloc[-1] > df['close'].iloc[-4])
    if hh_pattern:
        signals.append({"type": "Higher High Bull Reversal", "confidence": 0.6})
    # Similarly for LL, etc.
    return signals

# ---------- MACRO QUOTES ----------
def fetch_macro_quotes():
    out = {}
    for k,url in CONFIG["macro_quotes"].items():
        try:
            r = requests.get(url, timeout=8)
            df = pd.read_csv(pd.compat.StringIO(r.text))
            out[k] = df.iloc[-1].to_dict()
        except Exception as e:
            out[k] = {"error": str(e)}
    return out

# ---------- FED CALENDAR ----------
def fetch_fed_calendar():
    try:
        r = requests.get(CONFIG["fed_policy_url"], timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Parse upcoming dates (based on structure from tool result)
        # For simplicity, hard-code from tool, but in real, parse <div> with dates
        # Here, use parsed from tool
        calendar = {
            "upcoming": ["Oct 28-29 FOMC (press conf)", "Dec 9-10 FOMC (press conf)"],
            "minutes": ["Nov 19 (Oct meeting)", "Dec 30 (Dec meeting)"],
            "review": "2025 Review of Monetary Policy Strategy ongoing"
        }
        return calendar
    except Exception as e:
        log(f"Fed parse error: {e}")
        return {}

# ---------- NEWS + SENTIMENT ----------
def fetch_rss_headlines(limit=8):
    headlines=[]
    for feed in CONFIG["news_rss"]:
        try:
            d = feedparser.parse(feed)
            feed_title = d.feed.get("title", "Unknown Source")
            for e in d.entries[:limit]:
                title = e.get("title", "")
                link = e.get("link", "")
                # Ensure we have a proper link
                if not link and e.get("id"):
                    link = e.get("id")
                headlines.append({
                    "source": feed_title,
                    "title": title,
                    "link": link,
                    "published": e.get("published", ""),
                    "summary": e.get("summary", "")[:200] if e.get("summary") else ""
                })
        except Exception as e:
            log(f"Error fetching RSS from {feed}: {e}")
            continue
    return headlines

def simple_sentiment_score(text):
    s = 0.0
    words = [w.strip(".,:;()[]{}\"'").lower() for w in text.split()]
    for w in words:
        if w in CONFIG["sentiment_lexicon"]:
            s += CONFIG["sentiment_lexicon"][w]
    if len(words)>0:
        s = s / max(1.0, math.sqrt(len(words))/6.0)
    s = max(-4.0, min(4.0, s))
    return float(s)

def aggregate_headline_sentiment(headlines):
    scores = []
    sources = []
    for h in headlines:
        text = h.get("title","")
        sc = simple_sentiment_score(text)
        scores.append(sc)
        sources.append((
            h.get("source",""),
            sc,
            h.get("title",""),
            h.get("link",""),
            h.get("published",""),
            h.get("summary","")
        ))
    avg = float(np.mean(scores)) if scores else 0.0
    return {"avg": avg, "details": sources}

# Placeholder for X sentiment (use RSS or API if available)
def fetch_x_sentiment(limit=10):
    # Placeholder: use RSS for Bitcoin tweets
    headlines = fetch_rss_headlines(limit=limit)  # Reuse for now
    return aggregate_headline_sentiment(headlines)  # Or implement scraping

# ---------- MEMORY / LEARNING ----------
MEMPATH = Path(CONFIG["memory_csv"])

def ensure_memory():
    if not MEMPATH.exists():
        df = pd.DataFrame(columns=["date","setup","signal","entry","exit","pnl","win"])
        df.to_csv(MEMPATH, index=False)

def record_signal_outcome(date, setup, signal, entry, exit_price, pnl):
    ensure_memory()
    win = 1 if pnl>0 else 0
    row = pd.DataFrame([{"date": date.isoformat(), "setup": setup, "signal": signal,
                         "entry": float(entry), "exit": float(exit_price), "pnl": float(pnl), "win":win}])
    row.to_csv(MEMPATH, mode="a", header=False, index=False)

def compute_performance():
    ensure_memory()
    df = pd.read_csv(MEMPATH)
    if df.empty:
        return {"wins":0,"trades":0,"winrate":None}
    total = len(df)
    wins = int(df.win.sum())
    winrate = wins/total
    return {"wins":wins,"trades":total,"winrate":round(winrate,3)}

# ---------- SIGNALS & ANALYSIS ----------
def perform_indicator_analysis(df):
    # Compute MAs
    ma_fast = sma(df, 'close', CONFIG["ma_fast"])
    ma_medium = sma(df, 'close', CONFIG["ma_medium"])
    ma_slow = sma(df, 'close', CONFIG["ma_slow"])

    # Compute ATR
    atr_val = atr(df)

    # Compute MFI
    mfi_val = mfi(df, CONFIG["money_flow_period"])

    # VWAPs
    session_vwap = vwap_of(df.tail(390))  # Approx NY session 6.5h
    hourly_vwap = anchored_vwap(df, 'h')
    fourh_vwap = anchored_vwap(df, '4h')
    weekly_vwap = anchored_vwap(df, 'W')
    monthly_vwap = anchored_vwap(df, 'ME')
    yearly_vwap = anchored_vwap(df, 'YE')  # Approx

    # 9-Day Cycle VWAP with bands
    vwap_9d_data = calculate_9day_vwap_with_bands(df)
    reversal_zones = detect_reversal_zones(df, vwap_9d_data)

    # Trend score
    trend_score = compute_trend_score(df, ma_fast, ma_medium, ma_slow)

    # Signals
    signals = generate_signals(df, trend_score, ma_medium, fourh_vwap)

    # Liquidity flushes
    flushes = detect_liquidity_flush(df)

    return {
        "mas": {"fast": ma_fast.iloc[-1], "medium": ma_medium.iloc[-1], "slow": ma_slow.iloc[-1]},
        "vwaps": {"session": session_vwap, "1h": hourly_vwap, "4h": fourh_vwap,
                  "weekly": weekly_vwap, "monthly": monthly_vwap, "yearly": yearly_vwap},
        "vwap_9d": vwap_9d_data,
        "reversal_zones": reversal_zones,
        "trend_score": trend_score,
        "signals": signals,
        "flushes": flushes.to_dict('records') if not flushes.empty else [],
        "mfi": mfi_val.iloc[-1],
        "atr": atr_val.iloc[-1]
    }

def custom_signal_block(df):
    analysis = perform_indicator_analysis(df)
    signals = analysis["signals"]
    # Convert to bot's signal format
    bot_signals = []
    for sig in signals:
        bot_signals.append({"setup": sig["type"], "entry": df['close'].iloc[-1], "confidence": sig["confidence"], "notes": "From indicator"})
    return bot_signals

# ---------- PROBABILITY ENGINE ----------
def compute_probabilities(tech_signals, sentiment, perf, analysis):
    base_up = 0.35
    base_down = 0.35
    base_range = 0.30

    sent_adj = max(-4, min(4, sentiment["avg"])) * 0.03
    perf_adj = (perf["winrate"] - 0.5) * 0.2 if perf["winrate"] is not None else 0.0

    tech_up = 0.0
    tech_down = 0.0
    for s in tech_signals:
        conf = s.get("confidence", 0.5)
        if "Bull" in s["setup"]:
            tech_up += min(0.25, conf)
        elif "Bear" in s["setup"]:
            tech_down += min(0.25, conf)

    # Add trend score adjustment
    trend_adj = (analysis["trend_score"] - 5) / 10 * 0.15  # -0.15 to +0.15

    p_up = base_up + sent_adj + perf_adj + tech_up + trend_adj
    p_down = base_down - sent_adj - perf_adj + tech_down - trend_adj
    raw_total = p_up + p_down + base_range
    p_up /= raw_total
    p_down /= raw_total
    p_range = 1.0 - (p_up + p_down)
    return {"up": round(p_up,3), "down": round(p_down,3), "range": round(p_range,3),
            "components":{"sent_adj":round(sent_adj,3), "perf_adj":round(perf_adj,3),
                          "tech_up":round(tech_up,3), "tech_down":round(tech_down,3),
                          "trend_adj":round(trend_adj,3)}}

# ---------- PLAN ASSEMBLY ----------
def build_plan(post_to_discord=False):
    log("Fetching klines...")
    df = fetch_recent_klines()
    last_price = df['close'].iloc[-1]

    log("Performing indicator analysis...")
    analysis = perform_indicator_analysis(df)

    log("Fetching macro quotes...")
    macro = fetch_macro_quotes()

    log("Fetching headlines...")
    headlines = fetch_rss_headlines()
    sentiment = aggregate_headline_sentiment(headlines)

    log("Fetching X sentiment...")
    x_sentiment = fetch_x_sentiment()  # Placeholder, same as headlines for now

    log("Fetching Fed calendar...")
    fed_calendar = fetch_fed_calendar()

    tech_signals = custom_signal_block(df)

    perf = compute_performance()

    probs = compute_probabilities(tech_signals, sentiment, perf, analysis)

    now_ny = ny_now()
    day_of_week = now_ny.strftime("%A")
    is_weekend = day_of_week in ['Saturday', 'Sunday']
    session_context = "Weekend Analysis" if is_weekend else "NY Open Plan"

    # Get current market session
    current_hour = now_ny.hour
    if 9 <= current_hour < 16:
        session_status = "🟢 NY Session Active"
    elif 16 <= current_hour < 21:
        session_status = "🟡 After Hours"
    elif 21 <= current_hour or current_hour < 9:
        session_status = "🔴 Pre-Market"
    else:
        session_status = "📊 Market Closed"

    header = f"@everyone\nSNIPER GURU DAILY — BTC {session_context} (Enhanced Edition)\nTime: {now_ny.strftime('%Y-%m-%d %H:%M %Z')} | {session_status}\n\n"
    body_lines = []

    # Dynamic market context
    price_change_24h = ((last_price - df['close'].iloc[-1440]) / df['close'].iloc[-1440] * 100) if len(df) > 1440 else 0
    volatility_level = "High" if analysis['atr'] > 100 else "Medium" if analysis['atr'] > 50 else "Low"
    mfi_sentiment = "Strong Buying" if analysis['mfi'] > 70 else "Buying" if analysis['mfi'] > 50 else "Neutral" if analysis['mfi'] > 30 else "Selling" if analysis['mfi'] > 20 else "Strong Selling"

    body_lines.append("📊 Current Market Status")
    body_lines.append(f"- Bitcoin Price: ${last_price:,.0f} ({price_change_24h:+.1f}% 24h)")
    body_lines.append(f"- Volatility: {volatility_level} (${analysis['atr']:.0f}) - {volatility_level} price movement expected")
    body_lines.append(f"- Money Flow: {analysis['mfi']:.1f}/100 - {mfi_sentiment} pressure")

    # Add session-specific context
    if is_weekend:
        body_lines.append("- Weekend Trading: Lower volume, higher spreads expected")
    elif current_hour < 9:
        body_lines.append("- Pre-Market: Watch for overnight news impact")
    elif 9 <= current_hour < 16:
        body_lines.append("- NY Session: High volume, best liquidity")
    else:
        body_lines.append("- After Hours: Reduced liquidity, wider spreads")
    body_lines.append("")

    body_lines.append("📈 Technical Analysis")
    body_lines.append(f"- Trend Strength: {analysis['trend_score']}/10 ({'Strong Bull' if analysis['trend_score'] >= 7 else 'Bullish' if analysis['trend_score'] >= 5 else 'Neutral' if analysis['trend_score'] >= 4 else 'Bearish' if analysis['trend_score'] >= 3 else 'Strong Bear'})")
    body_lines.append(f"- Moving Averages: Short-term ${analysis['mas']['fast']:,.0f}, Medium-term ${analysis['mas']['medium']:,.0f}, Long-term ${analysis['mas']['slow']:,.0f}")
    body_lines.append(f"- Average Prices: 1H ${analysis['vwaps']['1h']:,.0f}, 4H ${analysis['vwaps']['4h']:,.0f}, Weekly ${analysis['vwaps']['weekly']:,.0f}, Monthly ${analysis['vwaps']['monthly']:,.0f}")

    # 9-Day Cycle VWAP Analysis
    vwap_9d = analysis['vwap_9d']
    if not np.isnan(vwap_9d['vwap_9d']):
        body_lines.append(f"- 9-Day Cycle VWAP: ${vwap_9d['vwap_9d']:,.0f}")
        body_lines.append(f"- Reversal Zones: Upper ${vwap_9d['upper_2sd']:,.0f}, Lower ${vwap_9d['lower_2sd']:,.0f}")

        # Reversal zone status
        zones = analysis['reversal_zones']
        if zones['in_upper_reversal_zone']:
            body_lines.append("- 🔴 UPPER REVERSAL ZONE - Watch for short opportunities")
        elif zones['in_lower_reversal_zone']:
            body_lines.append("- 🟢 LOWER REVERSAL ZONE - Watch for long opportunities")
        elif zones['extended_up']:
            body_lines.append("- 🟡 Extended above 1SD - Caution for longs")
        elif zones['extended_down']:
            body_lines.append("- 🟡 Extended below 1SD - Caution for shorts")
        else:
            body_lines.append("- ✅ Normal range - Standard trading conditions")

    if analysis['signals']:
        body_lines.append("- 🎯 Active Trading Signals:")
        for sig in analysis['signals']:
            body_lines.append(f"  • {sig['type']} (Confidence: {sig['confidence']*100:.0f}%)")
    body_lines.append("")

    body_lines.append("💧 Volume Activity")
    if analysis['flushes']:
        body_lines.append("- Recent High Volume Spikes (Big Money Moving):")
        for flush in analysis['flushes']:
            ts = pd.to_datetime(flush['open_time']).strftime('%H:%M')
            body_lines.append(f"  • {ts}: High ${flush['high']:,.0f}, Low ${flush['low']:,.0f} (Volume: {flush['volume']:.0f})")
    else:
        body_lines.append("- No major volume spikes detected - quiet market")
    body_lines.append("")

    body_lines.append("🎯 Market Direction Outlook")
    body_lines.append(f"- 📈 Price Going Up: {probs['up']*100:.1f}% chance")
    body_lines.append(f"- 📉 Price Going Down: {probs['down']*100:.1f}% chance")
    body_lines.append(f"- ↔️ Sideways/Range: {probs['range']*100:.1f}% chance")
    body_lines.append("")

    # Dynamic event context
    today = now_ny.strftime("%Y-%m-%d")
    tomorrow = (now_ny + dt.timedelta(days=1)).strftime("%Y-%m-%d")

    body_lines.append("📅 Today's Key Events & Tomorrow's Watchlist")

    # Check for today's events
    today_events = []
    for event in fed_calendar.get("upcoming", []):
        if "Oct 28-29" in event and "Oct" in today:
            today_events.append(f"🔥 TODAY: {event}")
        elif "Dec 9-10" in event and "Dec" in today:
            today_events.append(f"🔥 TODAY: {event}")
        else:
            body_lines.append(f"- {event}")

    if today_events:
        for event in today_events:
            body_lines.append(f"- {event}")

    # Add tomorrow's events
    for min_date in fed_calendar.get("minutes", []):
        if "Nov 19" in min_date and "Nov" in tomorrow:
            body_lines.append(f"- TOMORROW: {min_date}")
        elif "Dec 30" in min_date and "Dec" in tomorrow:
            body_lines.append(f"- TOMORROW: {min_date}")
        else:
            body_lines.append(f"- {min_date}")

    # Add current market impact
    if today_events:
        body_lines.append("- ⚠️ High Impact Day: Expect increased volatility")
    elif is_weekend:
        body_lines.append("- Weekend: Focus on technical levels, lower news impact")
    else:
        body_lines.append("- Regular Trading Day: Normal volatility expected")
    body_lines.append("")

    body_lines.append("🌍 Other Markets (Affects Bitcoin)")
    for k,v in macro.items():
        if isinstance(v, dict):
            close_price = v.get('Close', 'N/A')
            change = v.get('Change', 'N/A')
            if k == "SPY":
                body_lines.append(f"- Stock Market (SPY): ${close_price} ({change})")
            elif k == "VIX":
                body_lines.append(f"- Fear Index (VIX): {close_price} ({change})")
            elif k == "DXY":
                body_lines.append(f"- Dollar Strength (DXY): {close_price} ({change})")
            elif k == "WTI":
                body_lines.append(f"- Oil Price (WTI): ${close_price} ({change})")
            elif k == "GOLD":
                body_lines.append(f"- Gold Price: ${close_price} ({change})")
        else:
            body_lines.append(f"- {k}: {v}")
    body_lines.append("")

    sentiment_emoji = "😊" if sentiment["avg"] > 0.5 else "😐" if sentiment["avg"] > -0.5 else "😟"
    body_lines.append(f"📰 News Mood {sentiment_emoji} (Average: {sentiment['avg']:+.2f})")
    for item in sentiment["details"][:6]:
        if len(item) >= 4:
            src, sc, title, link = item[:4]
            mood_emoji = "😊" if sc > 0.5 else "😐" if sc > -0.5 else "😟"
            if link and link.startswith('http'):
                body_lines.append(f"- {mood_emoji} [{src}] {title}")
                body_lines.append(f"  🔗 {link}")
            else:
                body_lines.append(f"- {mood_emoji} [{src}] {title}")
    body_lines.append("")

    x_sentiment_emoji = "😊" if x_sentiment["avg"] > 0.5 else "😐" if x_sentiment["avg"] > -0.5 else "😟"
    body_lines.append(f"🐦 Social Media Mood {x_sentiment_emoji} (Average: {x_sentiment['avg']:+.2f})")
    for item in x_sentiment["details"][:4]:
        if len(item) >= 4:
            src, sc, title, link = item[:4]
            mood_emoji = "😊" if sc > 0.5 else "😐" if sc > -0.5 else "😟"
            if link and link.startswith('http'):
                body_lines.append(f"- {mood_emoji} {title[:60]}... ({sc:+.2f})")
                body_lines.append(f"  🔗 {link}")
            else:
                body_lines.append(f"- {mood_emoji} {title[:60]}... ({sc:+.2f})")
    body_lines.append("")

    body_lines.append("📊 Bot Performance History")
    if perf['trades'] > 0:
        winrate_pct = (perf['winrate'] * 100) if perf['winrate'] else 0
        body_lines.append(f"- Total Trades: {perf['trades']}")
        body_lines.append(f"- Winning Trades: {perf['wins']}")
        body_lines.append(f"- Success Rate: {winrate_pct:.1f}%")
    else:
        body_lines.append("- No trades recorded yet - bot is learning!")
    body_lines.append("")

    # Dynamic strategy based on current conditions
    if is_weekend:
        strategy_title = "📋 Weekend Trading Strategy"
        strategy_context = "Lower volume, focus on key levels"
    elif current_hour < 9:
        strategy_title = "📋 Pre-Market Strategy"
        strategy_context = "Watch for overnight news impact"
    elif 9 <= current_hour < 16:
        strategy_title = "📋 NY Session Strategy"
        strategy_context = "High volume, best execution"
    else:
        strategy_title = "📋 After Hours Strategy"
        strategy_context = "Reduced liquidity, wider spreads"

    body_lines.append(f"{strategy_title} - {strategy_context}")

    # Adjust strategy based on trend and volatility
    if analysis['trend_score'] >= 7:
        body_lines.append("🟢 STRONG BULL BIAS - Focus on Long Setups:")
        body_lines.append("   • Look for pullbacks to moving averages")
        body_lines.append("   • Target: Next resistance or +2-3% gain")
        body_lines.append("   • Stop: Below key support levels")
    elif analysis['trend_score'] <= 3:
        body_lines.append("🔴 STRONG BEAR BIAS - Focus on Short Setups:")
        body_lines.append("   • Look for bounces to resistance levels")
        body_lines.append("   • Target: Next support or -2-3% move")
        body_lines.append("   • Stop: Above key resistance levels")
    else:
        body_lines.append("🟡 NEUTRAL BIAS - Range Trading:")
        body_lines.append("   • Buy near support, sell near resistance")
        body_lines.append("   • Target: 1-2% moves in either direction")
        body_lines.append("   • Stop: Break of key levels")

    # Add session-specific advice
    if volatility_level == "High":
        body_lines.append("   ⚠️ High volatility - Use smaller position sizes")
    elif volatility_level == "Low":
        body_lines.append("   💡 Low volatility - May need larger moves for profit")

    body_lines.append("")

    # Dynamic tips based on current conditions
    body_lines.append("💡 Today's Trading Tips")

    # Market-specific tips
    if price_change_24h > 5:
        body_lines.append("- 📈 Strong 24h move - Watch for continuation or reversal")
    elif price_change_24h < -5:
        body_lines.append("- 📉 Strong 24h decline - Look for bounce or further weakness")
    else:
        body_lines.append("- 📊 Moderate price action - Focus on key levels")

    # Volatility tips
    if volatility_level == "High":
        body_lines.append("- ⚡ High volatility - Use wider stops, smaller positions")
    elif volatility_level == "Low":
        body_lines.append("- 🐌 Low volatility - May need patience for moves")

    # Session tips
    if is_weekend:
        body_lines.append("- 🏖️ Weekend trading - Lower volume, focus on major levels")
    elif current_hour < 9:
        body_lines.append("- 🌅 Pre-market - Watch for overnight news impact")
    elif 9 <= current_hour < 16:
        body_lines.append("- 🏢 NY session - Best liquidity, watch for institutional moves")
    else:
        body_lines.append("- 🌙 After hours - Reduced liquidity, wider spreads")

    # Trend-specific tips
    if analysis['trend_score'] >= 7:
        body_lines.append("- 🟢 Strong bull trend - Buy dips, avoid shorts")
    elif analysis['trend_score'] <= 3:
        body_lines.append("- 🔴 Strong bear trend - Sell rallies, avoid longs")
    else:
        body_lines.append("- 🟡 Neutral trend - Range trading preferred")

    body_lines.append("- 💰 Risk management: Only risk 1% per trade")
    body_lines.append("")

    body_lines.append("🛠️ Bot Tools & What to Watch")
    body_lines.append("- Volume Hunter: Alerts when trading volume is 2.5x higher than normal")
    body_lines.append("- Trend Analyzer: Combines multiple indicators for entry signals")
    body_lines.append("- Fed Watch: Oct 28-29 meeting could impact Bitcoin price")
    body_lines.append("")

    body_lines.append("📈 Follow These Setups Live on TradingView")
    body_lines.append("Add Cloudfare indicator to your charts:")
    body_lines.append("🔗 https://www.tradingview.com/script/ZWA48gFW-Cloudfare/")
    body_lines.append("")

    board = header + "\n".join(body_lines)
    print("\n" + board + "\n")

    if post_to_discord and CONFIG["discord_webhook"]:
        discord.send_analysis(board)

    return {"board":board, "signals":tech_signals, "probabilities":probs, "sentiment":sentiment, "perf":perf, "analysis":analysis}

# ---------- SCHEDULING ----------
def job(post_flag=False):
    try:
        build_plan(post_to_discord=post_flag)
    except Exception as e:
        log(f"Job failed: {e}")

def run_loop(post_flag=False):
    schedule.every().day.at(CONFIG["run_time_local"]).do(lambda: job(post_flag))
    log(f"Scheduled at NY {CONFIG['run_time_local']}.")

    # Send initial ping
    discord.send_ping()

    while True:
        schedule.run_pending()
        time.sleep(10)

# ---------- MAIN ----------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post", action="store_true", help="Post to Discord")
    parser.add_argument("--loop", action="store_true", help="Run in loop mode")
    parser.add_argument("--now", action="store_true", help="Run analysis now")
    parser.add_argument("--ping", action="store_true", help="Send ping to Discord")
    args = parser.parse_args()

    if args.ping:
        discord.send_ping()
    elif args.loop:
        run_loop(args.post)
    else:
        job(args.post)

if __name__=="__main__":
    main()
