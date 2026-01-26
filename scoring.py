from math import isfinite
from utils import fmt_price

def decide(v):
    # VWAP stack + momentum
    if v is None: return None
    price = v["h_close"]
    hv = v["h_vwap"]; dv = v["d_vwap"]
    rsi = v["h_rsi"]; macd = v["h_macd"]; sig = v["h_macdsig"]
    atr = max(v["h_atr"], 1e-6)

    long_bias = (price >= hv) and (hv >= dv) and (rsi < 65) and (macd >= sig)
    short_bias = (price <= hv) and (hv <= dv) and (rsi > 35) and (macd <= sig)

    score = 0
    why = []

    dist = abs(hv - dv) / max(dv, 1e-9)
    if long_bias:
        score += 4; why.append("1H VWAP ≥ Daily VWAP")
    if short_bias:
        score += 4; why.append("1H VWAP ≤ Daily VWAP")
    # momentum
    if macd >= sig:
        score += 2;
        if long_bias: why.append("MACD ≥ Signal")
    else:
        if short_bias:
            score += 2;
            why.append("MACD ≤ Signal")
    # RSI context
    if long_bias and rsi <= 55:
        score += 2; why.append("RSI not overbought")
    if short_bias and rsi >= 45:
        score += 2; why.append("RSI not oversold")

    # normalize to 10
    score = min(10, max(0, int(round(score + min(4, 10*dist)))))
    direction = "LONG" if (long_bias and score>=6 and not short_bias) else ("SHORT" if (short_bias and score>=6 and not long_bias) else None)
    if direction is None:
        return None

    # risk: ATR-based; GP proxy = 1.5% below/above entry or 1x ATR, whichever larger
    entry = price
    gp_buffer = max(0.015*entry, atr)
    if direction=="LONG":
        stop = entry - gp_buffer*1.0
        t1 = entry + 1.5*atr
        t2 = entry + 2.5*atr
    else:
        stop = entry + gp_buffer*1.0
        t1 = entry - 1.5*atr
        t2 = entry - 2.5*atr

    reason = " | ".join(why) + f" | dist(1H vs D) {dist*100:.1f}%"
    return dict(direction=direction, score=score, entry=entry, stop=stop, t1=t1, t2=t2, rsi=rsi, macd=macd, dist=dist, reason=reason)
