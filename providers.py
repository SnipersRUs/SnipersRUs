import pandas as pd, numpy as np, yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import AverageTrueRange

def fetch_df(ticker, period="6mo", interval="1d"):
    try:
        df = yf.download(
            ticker, period=period, interval=interval,
            auto_adjust=True, progress=False, threads=False
        )
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()
    # Normalize columns, drop weird multi-index if it appears
    if isinstance(df.columns, pd.MultiIndex):
        # pick first level if single ticker
        df.columns = [c[-1].title() for c in df.columns.to_flat_index()]
    else:
        df.columns = [c.title() for c in df.columns]
    keep = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
    df = df[keep].copy()
    # Ensure numeric & 1-D series
    for c in keep:
        s = df[c]
        if isinstance(s, pd.DataFrame):  # sometimes (N,1)
            s = s.iloc[:,0]
        df[c] = pd.to_numeric(s, errors="coerce")
    return df.dropna()

def _series(df, name):
    s = df[name]
    if isinstance(s, pd.DataFrame):
        s = s.iloc[:,0]
    s = pd.to_numeric(s, errors="coerce")
    return pd.Series(s.values.ravel(), index=df.index, name=name)

def add_indicators(df):
    if df is None or df.empty:
        return df
    close = _series(df,"Close")
    high  = _series(df,"High")
    low   = _series(df,"Low")
    vol   = _series(df,"Volume").fillna(0)

    # Indicators (ta expects 1-D Series)
    rsi  = RSIIndicator(close, window=14).rsi()
    macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
    atr  = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()

    # VWAP (session cumulative on given interval)
    tp = (high + low + close) / 3.0
    vol_cum = vol.replace(0, np.nan).cumsum()
    vwap = (tp * vol).cumsum() / vol_cum
    vwap = vwap.fillna(method="ffill")

    out = pd.DataFrame({
        "Open": _series(df,"Open") if "Open" in df.columns else close,
        "High": high, "Low": low, "Close": close, "Volume": vol,
        "RSI": rsi, "MACD": macd.macd(), "MACDsig": macd.macd_signal(),
        "ATR": atr, "VWAP": vwap
    }, index=df.index)
    return out.dropna(how="any")

def get_1h_vs_1d_vwap(ticker):
    h = add_indicators(fetch_df(ticker, period="10d", interval="60m"))
    d = add_indicators(fetch_df(ticker, period="6mo", interval="1d"))
    if h is None or d is None or h.empty or d.empty:
        return None
    try:
        return {
            "h_close": float(h["Close"].iloc[-1]),
            "d_close": float(d["Close"].iloc[-1]),
            "h_vwap": float(h["VWAP"].iloc[-1]),
            "d_vwap": float(d["VWAP"].iloc[-1]),
            "h_rsi": float(h["RSI"].iloc[-1]),
            "d_rsi": float(d["RSI"].iloc[-1]),
            "h_atr": float(h["ATR"].iloc[-1]),
            "d_atr": float(d["ATR"].iloc[-1]),
            "h_macd": float(h["MACD"].iloc[-1]),
            "h_macdsig": float(h["MACDsig"].iloc[-1]),
        }
    except Exception:
        return None

def news_blurbs():
    # lightweight macro headlines via yfinance
    tickers = ["SPY", "^VIX", "DXY", "CL=F", "ES=F", "NQ=F"]
    items = []
    try:
        for t in tickers:
            tk = yf.Ticker(t)
            for n in (tk.news or [])[:3]:
                title = n.get("title",""); link = n.get("link","")
                if title and link:
                    items.append((title, link))
    except Exception:
        pass
    uniq, seen = [], set()
    for t,l in items:
        if t not in seen:
            seen.add(t); uniq.append((t,l))
        if len(uniq) >= 6: break
    return uniq
