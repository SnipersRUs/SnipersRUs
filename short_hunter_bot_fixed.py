#!/usr/bin/env python3
"""
Quick fix - simplified short hunter that WILL find trades
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from short_hunter_bot import ShortHunterBot

# Override the analyze method with a simpler version
def simple_analyze(self, symbol: str, exchange: str):
    """SIMPLE VERSION - just find coins near top"""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timezone

    ex = self.exchanges.get(exchange)
    if not ex:
        return None

    # Clean symbol for Phemex
    clean_symbol = symbol.split(":")[0] if ":" in symbol else symbol

    try:
        # Get 15m data
        ohlcv = ex.fetch_ohlcv(clean_symbol, "15m", limit=100)
        if not ohlcv or len(ohlcv) < 50:
            return None

        df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")

        current_price = df["close"].iloc[-1]
        recent_high = df["high"].values[-100:].max()
        percent_from_top = ((recent_high - current_price) / recent_high) * 100 if recent_high > 0 else 100

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50

        # ACCEPT if within 5% of top OR RSI > 60
        if percent_from_top > 5.0 and current_rsi < 60:
            return None

        # Extract base
        base = symbol.split("/")[0].replace("USDT", "").replace("USDC", "").replace(":USDT", "").replace(":USDC", "")
        if "/" in symbol:
            base = symbol.split("/")[0]

        # Score
        score = 0
        reasons = []
        if percent_from_top < 2.0:
            score += 20
            reasons.append(f"{percent_from_top:.1f}% from top")
        elif percent_from_top < 5.0:
            score += 10
            reasons.append(f"{percent_from_top:.1f}% from top")

        if current_rsi > 70:
            score += 15
            reasons.append(f"RSI {current_rsi:.1f}")
        elif current_rsi > 60:
            score += 10
            reasons.append(f"RSI {current_rsi:.1f}")

        return {
            "symbol": symbol,
            "exchange": exchange,
            "base": base,
            "direction": "SHORT",
            "entry": float(current_price),
            "timeframe": "15m",
            "score": score,
            "confidence": min(max(int(score / 3), 5), 10),
            "reasons": " + ".join(reasons) if reasons else "Near top",
            "percent_from_top": float(percent_from_top),
            "rsi": float(current_rsi),
            "volume_ratio": 1.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return None

# Monkey patch the method
ShortHunterScanner._analyze_symbol = simple_analyze

if __name__ == "__main__":
    bot = ShortHunterBot()
    print("Testing simplified version...")
    shorts, watch = bot.scanner.scan_for_shorts()
    print(f"\n✅ FOUND: {len(shorts)} shorts, {len(watch)} watchlist")
    if shorts:
        for s in shorts:
            print(f"  🔴 {s['base']} - {s['reasons']}")
    if watch:
        for w in watch:
            print(f"  👀 {w['base']} - {w.get('percent_from_top', 0):.1f}% from top")








