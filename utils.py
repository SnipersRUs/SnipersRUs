import math, time, os
from datetime import datetime, timezone

WHITE   = 0xFFFFFF
BLUE    = 0x1D4ED8  # futures
ORANGE  = 0xF59E0B  # forex
RED     = 0xEF4444  # watchlist/news

def now_et_iso():
    # keep it simple; Discord shows local time anyway
    return datetime.now(timezone.utc).isoformat()

def fmt_price(x):
    try:
        f = float(x)
        # dynamic decimals for fx vs stocks
        if abs(f) >= 100:
            return f"{f:,.2f}"
        if abs(f) >= 1:
            return f"{f:,.3f}"
        return f"{f:,.5f}"
    except Exception:
        return "n/a"

def fmt_pct(x):
    try:
        return f"{float(x)*100:.1f}%"
    except:
        return "n/a"

def bullet(direction_bool):
    return "🟢" if direction_bool else "🔴"

def sleep_minutes(mins):
    for _ in range(mins):
        time.sleep(60)
