#!/usr/bin/env python3
"""
Top gainer analysis module for MMS trading system
Identifies high-volume, high-momentum coins for day trading
"""
import requests
import math
import time
from typing import Optional, Dict
from src.logger import err

EXCLUDE_TOKENS = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")

def _get(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make HTTP GET request with error handling
    """
    try:
        r = requests.get(url, params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        err("HTTP:", url, e)
        return None

def pick_coin_of_day(spot_base: str) -> Optional[Dict]:
    """
    Heuristic to find the best coin of the day:
    - From /ticker/24hr pick USDT pairs with quoteVolume > $20M
    - Exclude leveraged tokens (UP/DOWN/BULL/BEAR)
    - 24h change between +5% and +40%
    - Then compute last-60m change and pick the highest
    """
    rows = _get(f"{spot_base}/ticker/24hr") or []
    filt = []
    
    for r in rows:
        s = r.get("symbol", "")
        if not s.endswith("USDT") or any(s.endswith(x) for x in EXCLUDE_TOKENS):
            continue
        
        vol_quote = float(r.get("quoteVolume", 0.0))
        chg24 = float(r.get("priceChangePercent", 0.0))
        
        if vol_quote < 20_000_000:
            continue
        if not (5.0 <= chg24 <= 40.0):
            continue
        
        filt.append((s, vol_quote, chg24))
    
    if not filt:
        return None

    # Compute 60m change for top 20 by 24h change
    candidates = sorted(filt, key=lambda x: x[2], reverse=True)[:20]
    best = None
    best_h1 = -999
    
    for sym, volq, _ in candidates:
        k = _get(f"{spot_base}/klines", {"symbol": sym, "interval": "1m", "limit": 61}) or []
        if len(k) < 2:
            continue
        
        p0 = float(k[0][4])
        p1 = float(k[-1][4])
        h1 = (p1 - p0) / p0 * 100.0
        
        if h1 > best_h1:
            best_h1 = h1
            best = (sym, p1, h1, volq)
    
    if not best:
        return None

    sym, last_px, h1chg, volq = best
    return {
        "symbol": sym,
        "last": last_px,
        "h1chg": h1chg,
        "quoteVol": volq
    }













































