#!/usr/bin/env python3
"""
Short Hunter Bot - Finds the best SHORT opportunities at tops/resistances
- Scans for reversal setups at 15m+ timeframes
- Uses deviation VWAP (2σ = A+, 3σ = A++)
- Detects finished Wave 5 or SFPs as main catalyst
- Returns top 3 shorts per scan
- Scans every 60 minutes (1 hour)
"""
import os
import json
import time
import logging
import requests
import ccxt
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ShortHunter")

# Discord webhook from user
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1444925694290300938/ACddvkCxvrMz6I_LqbH7l4TOyhicCMh67g-kAtal8YPi0F-AZbXnZpYe7vzrQihJKo5X"

# Configuration
SCAN_INTERVAL_SEC = 60 * 60  # 60 minutes (1 hour)
MIN_TIMEFRAME = "15m"  # 15 minutes minimum
TIMEFRAMES = ["15m", "1h", "4h"]  # Scan these timeframes
MAX_SHORTS = 3  # Top 3 shorts per scan
# Watchlist removed per user request
MAX_OPEN_TRADES = 4  # Max 4 open trades
POSITION_SIZE_USD = 300.0  # $300 per trade
LEVERAGE = 15  # 15x leverage
STOP_LOSS_PCT = 0.02  # 2% stop loss
TAKE_PROFIT_PCT = 0.03  # 3% take profit
PNL_UPDATE_INTERVALS = [6, 12, 18, 0]  # 4 times per day (6am, 12pm, 6pm, midnight UTC)


def tv_link(symbol: str, exchange: str) -> str:
    """Generate TradingView link - use BINANCE format (most reliable)"""
    # BINANCE format works best: BINANCE:BTCUSDT (no slash)
    s = symbol.split(":")[0]  # drop trailing futures suffixes like :USDT or :USDC
    if "/" in s:
        base, quote = s.split("/", 1)
    else:
        # fallback: try to split on USDT or USDC
        if s.upper().endswith("USDT"):
            base, quote = s[:-4], "USDT"
        elif s.upper().endswith("USDC"):
            base, quote = s[:-4], "USDC"
        else:
            base, quote = s, "USDT"  # default to USDT
    # BINANCE format: BINANCE:BTCUSDT (no slash, most reliable)
    tv_symbol = f"BINANCE:{base.upper()}{quote.upper()}"
    return f"https://www.tradingview.com/chart/?symbol={tv_symbol}"


class DeviationVWAP:
    """Calculate VWAP with deviation bands (2σ, 3σ)"""

    def __init__(self, period: str = "daily"):
        self.period = period
        self.sum_pv = 0.0
        self.sum_v = 0.0
        self.sum_pv2 = 0.0
        self.last_reset = None

    def reset(self, current_time: pd.Timestamp):
        """Reset for new period"""
        if self.period == "daily":
            should_reset = self.last_reset is None or current_time.date() != self.last_reset.date()
        elif self.period == "weekly":
            should_reset = self.last_reset is None or current_time.isocalendar()[1] != self.last_reset.isocalendar()[1]
        elif self.period == "monthly":
            should_reset = self.last_reset is None or current_time.month != self.last_reset.month
        else:
            should_reset = False

        if should_reset:
            self.sum_pv = 0.0
            self.sum_v = 0.0
            self.sum_pv2 = 0.0
            self.last_reset = current_time
            return True
        return False

    def update(self, hlc3: float, volume: float, timestamp: pd.Timestamp):
        """Update VWAP calculations"""
        self.reset(timestamp)
        self.sum_pv += hlc3 * volume
        self.sum_v += volume
        self.sum_pv2 += (hlc3 ** 2) * volume

    def get_vwap_and_bands(self, dev_mult_1: float = 1.0, dev_mult_2: float = 2.0, dev_mult_3: float = 3.0) -> Dict:
        """Calculate VWAP and deviation bands"""
        if self.sum_v == 0:
            return None

        vwap = self.sum_pv / self.sum_v
        variance = (self.sum_pv2 / self.sum_v) - (vwap ** 2)
        std_dev = np.sqrt(max(variance, 0))

        if std_dev == 0:
            return None

        return {
            "vwap": vwap,
            "std_dev": std_dev,
            "upper_1": vwap + (std_dev * dev_mult_1),
            "lower_1": vwap - (std_dev * dev_mult_1),
            "upper_2": vwap + (std_dev * dev_mult_2),
            "lower_2": vwap - (std_dev * dev_mult_2),
            "upper_3": vwap + (std_dev * dev_mult_3),
            "lower_3": vwap - (std_dev * dev_mult_3),
        }

    def get_deviation_level(self, price: float) -> Tuple[int, float]:
        """Get deviation level (0, 1, 2, 3) and percentage"""
        bands = self.get_vwap_and_bands()
        if bands is None:
            return 0, 0.0

        vwap = bands["vwap"]
        std_dev = bands["std_dev"]

        if std_dev == 0:
            return 0, 0.0

        dev_percent = ((price - vwap) / std_dev)

        level = 0
        if price >= bands["upper_3"] or price <= bands["lower_3"]:
            level = 3
        elif price >= bands["upper_2"] or price <= bands["lower_2"]:
            level = 2
        elif price >= bands["upper_1"] or price <= bands["lower_1"]:
            level = 1

        return level, dev_percent


class ShortHunterScanner:
    """Scanner for SHORT opportunities at tops/resistances"""

    # ONLY these coins from avantisfinance Perps screenshots
    ALLOWED_COINS = {
        "BERA", "NEAR", "ENA", "APT", "OP", "ARB", "TRUMP", "ONDO", "GOAT",
        "BNB", "ASTER", "DYM", "SUI", "LDO", "AAVE", "VIRTUAL", "WLD", "MON",
        "ZEC", "LINK", "AERO", "TAO", "KAITO", "ZK", "EIGEN", "ZRO", "ETHFI",
        "CHILLGUY", "PENDLE", "PENGU", "APE", "BTC", "ETH", "SOL", "HYPE",
        "XRP", "PEPE", "FARTCOIN", "DOGE", "WIF", "REZ", "POL", "XMR", "PUMP",
        "AVAX", "POPCAT", "XPL", "TIA", "SHIB", "BONK", "ZORA", "AVNT"
    }

    def __init__(self, exchanges: Dict[str, ccxt.Exchange]):
        self.exchanges = exchanges
        self.watchlist = self._build_watchlist()

    def _build_watchlist(self) -> List[Dict]:
        """Build watchlist of ONLY coins from avantisfinance Perps screenshots"""
        items: List[Dict] = []

        # Use MEXC exchange
        ex = self.exchanges.get("mexc")
        if not ex:
            logger.error("MEXC exchange not found!")
            return []

        def extract_base_symbol(symbol: str) -> str:
            """Extract base symbol from MEXC symbol format"""
            # Handle formats like: BTC/USDT:USDT, BTC/USDT, BTC:USDT:USDT, etc.
            # Remove all suffixes and get just the base
            s = symbol.upper()

            # Remove common suffixes
            for suffix in [":USDT:USDT", ":USDC:USDC", "/USDT:USDT", "/USDC:USDC",
                          ":USDT", ":USDC", "/USDT", "/USDC"]:
                if s.endswith(suffix):
                    s = s[:-len(suffix)]
                    break

            # If still has slash, take first part
            if "/" in s:
                s = s.split("/")[0]

            # If still has colon, take first part
            if ":" in s:
                s = s.split(":")[0]

            return s

        # Build symbol map for allowed coins ONLY
        syms = []
        found_bases = set()
        for s, m in ex.markets.items():
            try:
                # Look for perpetual swaps (both USDT and USDC)
                if (m.get("type") == "swap" and
                    m.get("active", True) and
                    not s.endswith(":USDT:USDT") and  # Avoid double USDT suffixes
                    not s.endswith(":USDC:USDC")):  # Avoid double USDC suffixes

                    # Extract base symbol properly
                    base = extract_base_symbol(s)

                    # STRICT CHECK: Only include if base is in allowed list
                    if base in self.ALLOWED_COINS:
                        syms.append(s)
                        found_bases.add(base)
            except Exception as e:
                logger.debug(f"Error processing symbol {s}: {e}")
                continue

        # Log what we found
        missing = self.ALLOWED_COINS - found_bases
        if missing:
            logger.warning(f"⚠️  Could not find these coins on MEXC: {sorted(missing)}")
        logger.info(f"✅ Found {len(found_bases)}/{len(self.ALLOWED_COINS)} allowed coins: {sorted(found_bases)}")

        volmap: Dict[str, float] = {}
        try:
            tickers = ex.fetch_tickers()
            for sym, t in tickers.items():
                if sym not in syms:
                    continue
                last = float(t.get("last") or t.get("close") or 0) or 0.0
                qv = t.get("quoteVolume")
                if qv is None:
                    bv = float(t.get("baseVolume") or 0.0)
                    usd24 = bv * last
                else:
                    usd24 = float(qv or 0.0)
                volmap[sym] = usd24
        except Exception:
            pass

        for sym in syms:
            # Extract base symbol properly
            base = extract_base_symbol(sym)

            # DOUBLE CHECK: Only add if base is in allowed list
            if base in self.ALLOWED_COINS:
                items.append({
                    "symbol": sym,
                    "exchange": "mexc",
                    "base": base,
                    "usd24": float(volmap.get(sym, 0.0))
                })

        items.sort(key=lambda x: x.get("usd24", 0.0), reverse=True)

        # Log all coins in watchlist for verification
        watchlist_bases = sorted([item["base"] for item in items])
        logger.info(f"✅ Built watchlist: {len(items)} futures pairs on MEXC (ONLY avantisfinance Perps coins)")
        logger.info(f"📋 Watchlist coins: {', '.join(watchlist_bases)}")

        # Verify all are in allowed list
        invalid = [item["base"] for item in items if item["base"] not in self.ALLOWED_COINS]
        if invalid:
            logger.error(f"❌ ERROR: Found invalid coins in watchlist: {invalid}")
            # Remove invalid coins
            items = [item for item in items if item["base"] in self.ALLOWED_COINS]
            logger.info(f"✅ Cleaned watchlist: {len(items)} valid coins remaining")

        return items

    def _get_ohlcv_data(self, ex: ccxt.Exchange, symbol: str, timeframe: str = "15m", limit: int = 200) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data - fix Phemex symbol format"""
        try:
            # Phemex needs symbol without the :USDT:USDT suffix
            # Convert BTC/USDT:USDT -> BTC/USDT
            clean_symbol = symbol
            if ":USDT" in clean_symbol:
                clean_symbol = clean_symbol.split(":")[0]
            if ":USDC" in clean_symbol:
                clean_symbol = clean_symbol.split(":")[0]

            ohlcv = ex.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
            if not ohlcv or len(ohlcv) == 0:
                return None
            df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
            df.set_index("ts", inplace=True)
            return df
        except Exception as e:
            logger.debug(f"Error fetching {symbol} {timeframe}: {e}")
            return None

    def _calculate_vwap_deviations(self, df: pd.DataFrame) -> Dict:
        """Calculate daily, weekly, monthly VWAP deviations"""
        if len(df) < 50:
            return {}

        daily_vwap = DeviationVWAP("daily")
        weekly_vwap = DeviationVWAP("weekly")
        monthly_vwap = DeviationVWAP("monthly")

        # Update VWAPs for each candle
        for idx, row in df.iterrows():
            hlc3 = (row["high"] + row["low"] + row["close"]) / 3
            daily_vwap.update(hlc3, row["volume"], idx)
            weekly_vwap.update(hlc3, row["volume"], idx)
            monthly_vwap.update(hlc3, row["volume"], idx)

        current_price = df["close"].iloc[-1]

        daily_bands = daily_vwap.get_vwap_and_bands()
        weekly_bands = weekly_vwap.get_vwap_and_bands()
        monthly_bands = monthly_vwap.get_vwap_and_bands()

        result = {}

        if daily_bands:
            daily_level, daily_pct = daily_vwap.get_deviation_level(current_price)
            result["daily"] = {
                "level": daily_level,
                "percent": daily_pct,
                "vwap": daily_bands["vwap"],
                "upper_2": daily_bands["upper_2"],
                "upper_3": daily_bands["upper_3"],
            }

        if weekly_bands:
            weekly_level, weekly_pct = weekly_vwap.get_deviation_level(current_price)
            result["weekly"] = {
                "level": weekly_level,
                "percent": weekly_pct,
                "vwap": weekly_bands["vwap"],
                "upper_2": weekly_bands["upper_2"],
                "upper_3": weekly_bands["upper_3"],
            }

        if monthly_bands:
            monthly_level, monthly_pct = monthly_vwap.get_deviation_level(current_price)
            result["monthly"] = {
                "level": monthly_level,
                "percent": monthly_pct,
                "vwap": monthly_bands["vwap"],
                "upper_2": monthly_bands["upper_2"],
                "upper_3": monthly_bands["upper_3"],
            }

        return result

    def _detect_wave_5_completion(self, df: pd.DataFrame) -> bool:
        """Detect if Wave 5 is complete (looking for 5-wave pattern completion)"""
        if len(df) < 100:
            return False

        # Simplified Wave 5 detection:
        # Look for 5 distinct higher highs in recent price action
        # Wave 5 should be the final move before reversal

        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        # Find pivot highs (local maxima)
        pivot_highs = []
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                pivot_highs.append((i, highs[i]))

        if len(pivot_highs) < 5:
            return False

        # Check if we have 5 ascending waves
        recent_pivots = pivot_highs[-5:]
        is_ascending = True
        for i in range(1, len(recent_pivots)):
            if recent_pivots[i][1] <= recent_pivots[i-1][1]:
                is_ascending = False
                break

        # Wave 5 should be near completion (price starting to reject)
        if is_ascending and len(recent_pivots) >= 5:
            last_high = recent_pivots[-1][1]
            current_price = closes[-1]
            # Price should be near the high but showing signs of rejection
            rejection = (last_high - current_price) / last_high > 0.01  # 1% rejection
            return rejection

        return False

    def _detect_sfp(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect Fair Value Gaps (SFPs) - looking for bearish SFPs for shorts"""
        if len(df) < 3:
            return None

        # Look for bearish FVG: gap down (previous low > current high)
        for i in range(2, len(df)):
            prev_low = df["low"].iloc[i-1]
            curr_high = df["high"].iloc[i]

            # Bearish FVG detected
            if prev_low > curr_high:
                gap_top = prev_low
                gap_bottom = curr_high
                current_price = df["close"].iloc[-1]

                # Check if price is at or near the gap (good short entry)
                if gap_bottom <= current_price <= gap_top:
                    return {
                        "type": "BEARISH",
                        "gap_top": gap_top,
                        "gap_bottom": gap_bottom,
                        "at_gap": True
                    }
                elif current_price > gap_top:
                    # Price above gap, approaching from above
                    distance = ((current_price - gap_top) / current_price) * 100
                    if distance <= 2.0:  # Within 2%
                        return {
                            "type": "BEARISH",
                            "gap_top": gap_top,
                            "gap_bottom": gap_bottom,
                            "at_gap": False,
                            "distance_pct": distance
                        }

        return None

    def _detect_bearish_sfp_alert(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect bearish Swing Failure Pattern (SFP) - price breaks high then reverses"""
        if len(df) < 30:
            return None

        # Look for pivot highs in the last 50 bars
        lookback = min(50, len(df) - 5)
        highs = df["high"].values[-lookback:]
        closes = df["close"].values[-lookback:]

        # Find pivot highs (local maxima with at least 3 bars on each side)
        pivot_highs = []
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                pivot_highs.append((i, highs[i]))

        if not pivot_highs:
            return None

        # Check each pivot high for SFP pattern
        for pivot_idx, pivot_high in pivot_highs[-3:]:  # Check last 3 pivot highs
            # Check if price broke above this pivot and then reversed
            broke_above = False
            break_idx = None
            reversal_confirmed = False

            # Look for break above pivot after the pivot was formed
            for i in range(pivot_idx + 1, len(highs)):
                if highs[i] > pivot_high * 1.0005:  # Broke above by 0.05%
                    broke_above = True
                    break_idx = i
                    break

            if broke_above and break_idx is not None:
                # Check if price reversed (closed below pivot) after breaking above
                for i in range(break_idx + 1, min(break_idx + 8, len(closes))):
                    if closes[i] < pivot_high * 0.9995:  # Closed below pivot by 0.05%
                        reversal_confirmed = True
                        reversal_idx = i
                        break

                if reversal_confirmed:
                    # Calculate current position
                    current_price = df["close"].iloc[-1]
                    current_idx = len(df) - 1
                    bars_since_break = current_idx - (len(df) - lookback + break_idx)
                    bars_since_reversal = current_idx - (len(df) - lookback + reversal_idx)

                    # Only alert if reversal happened recently (within last 10 bars)
                    if bars_since_reversal <= 10:
                        # Calculate SFP probability score
                        score = 50  # Base score

                        # Recent reversal (higher score)
                        if bars_since_reversal <= 3:
                            score += 30
                        elif bars_since_reversal <= 6:
                            score += 20
                        elif bars_since_reversal <= 10:
                            score += 10

                        # Strong reversal (close well below pivot)
                        reversal_strength = ((pivot_high - current_price) / pivot_high) * 100
                        if reversal_strength > 1.5:
                            score += 25
                        elif reversal_strength > 1.0:
                            score += 20
                        elif reversal_strength > 0.5:
                            score += 15
                        elif reversal_strength > 0.2:
                            score += 10

                        # Volume confirmation
                        recent_volume = df["volume"].iloc[-3:].mean()
                        avg_volume = df["volume"].rolling(20).mean().iloc[-1]
                        if recent_volume > avg_volume * 1.5:
                            score += 20
                        elif recent_volume > avg_volume * 1.2:
                            score += 15
                        elif recent_volume > avg_volume:
                            score += 10

                        # RSI confirmation (overbought then reversing)
                        delta = df["close"].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                        rs = gain / loss.replace(0, np.nan)
                        rsi = 100 - (100 / (1 + rs))
                        current_rsi = rsi.iloc[-1] if not rsi.empty else 50

                        if current_rsi > 60:
                            score += 10

                        # Only return if score is high enough
                        if score >= 60:
                            return {
                                "pivot_high": pivot_high,
                                "current_price": current_price,
                                "reversal_strength": reversal_strength,
                                "score": score,
                                "bars_since_break": bars_since_break,
                                "bars_since_reversal": bars_since_reversal
                            }

        return None

    def _detect_three_crows(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Three Crows pattern detection has been disabled per user request.

        This method is kept as a stub (always returns None) so any legacy calls
        safely do nothing and NO Three Crows alerts are ever produced.
        """
        return None

    def _detect_topping_breakdown(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect topping pattern followed by breakdown - potential downside runner"""
        if len(df) < 30:
            return None

        # Look for recent high (top)
        lookback = min(50, len(df))
        recent_data = df.iloc[-lookback:]

        # Find the highest point in recent data
        max_idx = recent_data["high"].idxmax()
        max_high = recent_data["high"].max()
        max_price = recent_data.loc[max_idx, "close"]

        # Check if this high was recent (within last 20 bars)
        bars_since_high = len(df) - 1 - df.index.get_loc(max_idx)

        if bars_since_high > 20:
            return None

        # Check if price has broken down significantly from the high
        current_price = df["close"].iloc[-1]
        decline_from_high = ((max_high - current_price) / max_high) * 100

        # Need significant decline (at least 3%)
        if decline_from_high < 3.0:
            return None

        # Check if there was a topping pattern (consolidation near high before breakdown)
        # Look for price staying near high for a few bars, then breaking down
        high_period = recent_data.loc[df.index.get_loc(max_idx)-2:df.index.get_loc(max_idx)+2]
        was_near_high = (high_period["close"] > max_high * 0.98).any()

        # Check for breakdown (recent lower lows)
        recent_lows = df["low"].iloc[-5:].values
        if len(recent_lows) < 3:
            return None

        # Check if making lower lows (breakdown pattern)
        making_lower_lows = all(recent_lows[i] < recent_lows[i-1] for i in range(1, len(recent_lows)))

        if was_near_high and making_lower_lows:
            # Calculate pattern strength
            score = 60  # Base score

            # Significant decline
            if decline_from_high > 10.0:
                score += 25
            elif decline_from_high > 7.0:
                score += 20
            elif decline_from_high > 5.0:
                score += 15
            elif decline_from_high > 3.0:
                score += 10

            # Volume on breakdown
            avg_volume = df["volume"].rolling(20).mean().iloc[-1]
            breakdown_volume = df["volume"].iloc[-5:].mean()
            if breakdown_volume > avg_volume * 1.5:
                score += 15
            elif breakdown_volume > avg_volume * 1.2:
                score += 10

            # RSI confirmation
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50

            if current_rsi < 50:  # Oversold but still declining
                score += 10

            return {
                "pattern": "TOPPING_BREAKDOWN",
                "score": score,
                "high_price": max_high,
                "current_price": current_price,
                "decline_pct": decline_from_high,
                "bars_since_high": bars_since_high,
                "rsi": current_rsi,
                "volume_ratio": breakdown_volume / avg_volume if avg_volume > 0 else 1.0
            }

        return None

    def _find_resistance_levels(self, df: pd.DataFrame, lookback: int = 100) -> List[float]:
        """Find resistance levels (pivot highs)"""
        if len(df) < lookback:
            lookback = len(df)

        highs = df["high"].values[-lookback:]

        # Find pivot highs
        resistances = []
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                resistances.append(highs[i])

        # Cluster nearby resistances
        if not resistances:
            return []

        resistances.sort(reverse=True)
        clustered = []
        for r in resistances:
            if not clustered or abs(r - clustered[-1]) / clustered[-1] > 0.02:  # 2% difference
                clustered.append(r)

        return clustered[:5]  # Top 5 resistance levels

    def _calculate_percent_from_top(self, current_price: float, df: pd.DataFrame, lookback: int = 200) -> float:
        """Calculate percentage from recent top"""
        if len(df) < lookback:
            lookback = len(df)

        recent_high = df["high"].values[-lookback:].max()
        if recent_high == 0:
            return 0.0

        percent_from_top = ((recent_high - current_price) / recent_high) * 100
        return percent_from_top

    def _analyze_symbol(self, symbol: str, exchange: str) -> Optional[Dict]:
        """Analyze symbol for SHORT opportunities - SIMPLIFIED VERSION"""
        # CRITICAL: Extract base symbol and check if it's allowed BEFORE doing any work
        def extract_base_symbol(symbol: str) -> str:
            """Extract base symbol from MEXC symbol format"""
            s = symbol.upper()
            for suffix in [":USDT:USDT", ":USDC:USDC", "/USDT:USDT", "/USDC:USDC",
                          ":USDT", ":USDC", "/USDT", "/USDC"]:
                if s.endswith(suffix):
                    s = s[:-len(suffix)]
                    break
            if "/" in s:
                s = s.split("/")[0]
            if ":" in s:
                s = s.split(":")[0]
            return s

        base = extract_base_symbol(symbol)

        # STRICT FILTER: Reject immediately if not in allowed list
        if base not in self.ALLOWED_COINS:
            logger.debug(f"🚫 Rejected {symbol} (base: {base}) - not in allowed list")
            return None

        ex = self.exchanges.get(exchange)
        if not ex:
            return None

        # Try 15m timeframe first (fastest)
        df = self._get_ohlcv_data(ex, symbol, "15m", limit=100)
        if df is None or len(df) < 50:
            return None

        current_price = df["close"].iloc[-1]
        volume = df["volume"].iloc[-1]
        avg_volume = df["volume"].rolling(20).mean().iloc[-1]
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # SIMPLE: Calculate percent from top (most important for shorts)
        recent_high = df["high"].values[-100:].max()
        percent_from_top = ((recent_high - current_price) / recent_high) * 100 if recent_high > 0 else 100

        # Calculate RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50

        # SIMPLE CRITERIA: Accept if within 5% of top OR RSI > 60
        if percent_from_top > 5.0 and current_rsi < 60:
            return None

        # Find resistance levels
        resistances = self._find_resistance_levels(df)
        near_resistance = False
        resistance_distance = 0.0
        if resistances:
            nearest_res = resistances[0]
            resistance_distance = ((current_price - nearest_res) / nearest_res) * 100
            if abs(resistance_distance) <= 2.0:
                near_resistance = True

        # Detect Wave 5 and SFP (optional)
        wave_5_complete = self._detect_wave_5_completion(df)
        sfp = self._detect_sfp(df)

        # Calculate VWAP deviations (optional, for scoring)
        vwap_data = self._calculate_vwap_deviations(df)
        max_dev_level = 0
        max_dev_pct = 0.0
        dev_source = None

        if vwap_data:
            for period, data in vwap_data.items():
                if data["level"] > max_dev_level:
                    max_dev_level = data["level"]
                    max_dev_pct = data["percent"]
                    dev_source = period
                elif data["level"] == max_dev_level and abs(data["percent"]) > abs(max_dev_pct):
                    max_dev_pct = data["percent"]
                    dev_source = period

        # Score the setup
        score = 0
        reasons = []

        # Percent from top (main factor for shorts)
        if percent_from_top < 1.0:
            score += 25
            reasons.append(f"{percent_from_top:.1f}% from top")
        elif percent_from_top < 2.0:
            score += 20
            reasons.append(f"{percent_from_top:.1f}% from top")
        elif percent_from_top < 5.0:
            score += 15
            reasons.append(f"{percent_from_top:.1f}% from top")

        # RSI
        if current_rsi > 70:
            score += 15
            reasons.append(f"RSI {current_rsi:.1f}")
        elif current_rsi > 60:
            score += 10
            reasons.append(f"RSI {current_rsi:.1f}")

        # Deviation VWAP
        if max_dev_level >= 3:
            score += 20
            reasons.append(f"3σ {dev_source.upper()} VWAP")
        elif max_dev_level >= 2:
            score += 15
            reasons.append(f"2σ {dev_source.upper()} VWAP")
        elif max_dev_level >= 1:
            score += 10
            reasons.append(f"1σ {dev_source.upper()} VWAP")

        # Wave 5 and SFP
        if wave_5_complete:
            score += 15
            reasons.append("Wave 5")
        if sfp:
            score += 10
            reasons.append("SFP")
        if near_resistance:
            score += 10
            reasons.append("Resistance")

        # Volume
        if volume_ratio > 1.5:
            score += 5
            reasons.append(f"Vol {volume_ratio:.1f}x")

        # Base symbol already extracted and validated at start of function
        # (no need to re-extract, but keeping for clarity)

        # ENHANCED ENTRY PRICE: Use resistance level or recent high for better entry
        # For shorts, we want to enter on pullback to resistance, not at current price
        optimal_entry = current_price

        if resistances:
            nearest_res = resistances[0]
            # If we're near resistance, use resistance as entry (pullback entry)
            if abs(resistance_distance) <= 1.0:  # Within 1% of resistance
                optimal_entry = nearest_res
            # If price is above resistance, wait for pullback to resistance
            elif resistance_distance > 0:
                optimal_entry = nearest_res * 1.002  # Slightly above resistance for entry
        else:
            # No clear resistance, use recent high as entry target
            if percent_from_top < 2.0:
                optimal_entry = recent_high * 0.998  # Slightly below recent high

        return {
            "symbol": symbol,
            "exchange": exchange,
            "base": base,
            "direction": "SHORT",
            "entry": float(optimal_entry),  # Use optimal entry instead of current price
            "current_price": float(current_price),  # Store current price separately
            "timeframe": "15m",
            "score": score,
            "confidence": min(max(int(score / 3), 5), 10),  # Minimum 5/10 confidence
            "reasons": " + ".join(reasons) if reasons else "Near top",
            "deviation_level": max_dev_level,
            "deviation_source": dev_source or "N/A",
            "deviation_percent": float(max_dev_pct),
            "wave_5_complete": wave_5_complete,
            "sfp": sfp is not None,
            "near_resistance": near_resistance,
            "resistance_distance": float(resistance_distance),
            "percent_from_top": float(percent_from_top),
            "rsi": float(current_rsi),
            "volume_ratio": float(volume_ratio),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def scan_for_shorts(self) -> List[Dict]:
        """Scan markets for SHORT opportunities"""
        logger.info(f"🔍 Scanning {len(self.watchlist)} markets for SHORT opportunities...")

        signals = []
        for item in self.watchlist:
            try:
                # SAFETY CHECK: Only process allowed coins
                base = item.get("base", "").upper()
                if base not in self.ALLOWED_COINS:
                    logger.warning(f"⚠️  Skipping {base} - not in allowed list!")
                    continue

                signal = self._analyze_symbol(item["symbol"], item["exchange"])
                if signal:
                    # DOUBLE CHECK: Verify signal base is in allowed list
                    signal_base = signal.get("base", "").upper()
                    if signal_base in self.ALLOWED_COINS:
                        signals.append(signal)
                        logger.info(f"📊 {signal['base']} SHORT ({signal['confidence']}/10) — {signal['reasons']}")
                    else:
                        logger.warning(f"⚠️  Rejected signal for {signal_base} - not in allowed list!")
                time.sleep(0.05)  # Rate limit
            except Exception as e:
                logger.debug(f"Error scanning {item['symbol']}: {e}")
                continue

        # Sort by score (confidence)
        signals.sort(key=lambda x: (x.get("score", 0), x.get("deviation_level", 0)), reverse=True)

        # Top shorts (best setups) - take top 3 by score
        top_shorts = signals[:MAX_SHORTS] if signals else []

        logger.info(f"✅ Found {len(top_shorts)} shorts")
        return top_shorts

    def scan_for_sfp_alerts(self) -> List[Dict]:
        """Scan for bearish SFP (Swing Failure Pattern) alerts - top 3 most probable"""
        logger.info("🔍 Scanning for bearish SFP alerts...")

        sfp_alerts = []
        for item in self.watchlist:
            try:
                # SAFETY CHECK: Only process allowed coins
                base = item.get("base", "").upper()
                if base not in self.ALLOWED_COINS:
                    continue

                ex = self.exchanges.get(item["exchange"])
                if not ex:
                    continue

                # Get 15m data for SFP detection
                df = self._get_ohlcv_data(ex, item["symbol"], "15m", limit=100)
                if df is None or len(df) < 50:
                    continue

                # Detect SFP
                sfp_data = self._detect_bearish_sfp_alert(df)
                if sfp_data and sfp_data.get("score", 0) >= 60:  # Minimum score threshold
                    current_price = df["close"].iloc[-1]

                    # Calculate RSI for context
                    delta = df["close"].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss.replace(0, np.nan)
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1] if not rsi.empty else 50

                    # Get volume ratio
                    volume = df["volume"].iloc[-1]
                    avg_volume = df["volume"].rolling(20).mean().iloc[-1]
                    volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

                    alert = {
                        "symbol": item["symbol"],
                        "base": item["base"],
                        "exchange": item["exchange"],
                        "timeframe": "15m",
                        "pivot_high": sfp_data["pivot_high"],
                        "current_price": current_price,
                        "reversal_strength": sfp_data["reversal_strength"],
                        "score": sfp_data["score"],
                        "rsi": current_rsi,
                        "volume_ratio": volume_ratio,
                        "bars_since_break": sfp_data["bars_since_break"]
                    }
                    sfp_alerts.append(alert)
                    logger.info(f"⚠️ {item['base']} SFP Alert (Score: {sfp_data['score']})")

                time.sleep(0.05)  # Rate limit
            except Exception as e:
                logger.debug(f"Error scanning SFP for {item['symbol']}: {e}")
                continue

        # Sort by score and take top 3
        sfp_alerts.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_sfps = sfp_alerts[:3]

        logger.info(f"✅ Found {len(top_sfps)} SFP alerts")
        return top_sfps

    def scan_for_bearish_patterns(self) -> List[Dict]:
        """Scan for Topping Breakdown patterns - high-end short opportunities"""
        logger.info("🔍 Scanning for bearish reversal patterns (Topping Breakdown)...")

        pattern_alerts = []
        for item in self.watchlist:
            try:
                # SAFETY CHECK: Only process allowed coins
                base = item.get("base", "").upper()
                if base not in self.ALLOWED_COINS:
                    continue

                ex = self.exchanges.get(item["exchange"])
                if not ex:
                    continue

                # Get 15m data for pattern detection
                df = self._get_ohlcv_data(ex, item["symbol"], "15m", limit=100)
                if df is None or len(df) < 30:
                    continue

                # Detect Topping Breakdown pattern
                topping_breakdown = self._detect_topping_breakdown(df)
                if topping_breakdown and topping_breakdown.get("score", 0) >= 70:  # High threshold
                    current_price = df["close"].iloc[-1]

                    alert = {
                        "symbol": item["symbol"],
                        "base": item["base"],
                        "exchange": item["exchange"],
                        "timeframe": "15m",
                        "pattern": "TOPPING_BREAKDOWN",
                        "pattern_name": "Topping Breakdown",
                        "score": topping_breakdown["score"],
                        "current_price": current_price,
                        "high_price": topping_breakdown["high_price"],
                        "decline_pct": topping_breakdown["decline_pct"],
                        "bars_since_high": topping_breakdown["bars_since_high"],
                        "rsi": topping_breakdown["rsi"],
                        "volume_ratio": topping_breakdown["volume_ratio"]
                    }
                    pattern_alerts.append(alert)
                    logger.info(f"🔴 {item['base']} TOPPING BREAKDOWN Alert (Score: {topping_breakdown['score']})")

                time.sleep(0.05)  # Rate limit
            except Exception as e:
                logger.debug(f"Error scanning patterns for {item['symbol']}: {e}")
                continue

        # Sort by score and take top 5 (most significant)
        pattern_alerts.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_patterns = pattern_alerts[:5]

        logger.info(f"✅ Found {len(top_patterns)} bearish pattern alerts")
        return top_patterns


class PaperTrader:
    """Paper trading system for Short Hunter"""

    def __init__(self, state_path: str = "short_hunter_state.json"):
        self.state_path = state_path
        self.state = self._load_state()
        self.last_pnl_update_hour = None

    def _load_state(self) -> Dict:
        """Load trading state"""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "balance": 10000.0,
            "trades": [],
            "history": [],
            "pending_signals": [],  # Signals waiting for entry
            "stats": {
                "wins": 0,
                "losses": 0,
                "realized_pnl": 0.0,
                "total_pnl": 0.0,
                "daily_pnl": 0.0
            }
        }

    def _save_state(self):
        """Save trading state"""
        def convert_to_serializable(obj):
            """Convert numpy types and other non-serializable types to Python native types"""
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            return obj

        try:
            serializable_state = convert_to_serializable(self.state)
            with open(self.state_path, 'w') as f:
                json.dump(serializable_state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}", exc_info=True)

    def can_open_trade(self, base: str) -> bool:
        """Check if we can open a new trade"""
        open_trades = [t for t in self.state["trades"] if t.get("status") == "OPEN"]
        if len(open_trades) >= MAX_OPEN_TRADES:
            return False
        # Check for duplicate ticker
        for trade in open_trades:
            if trade.get("base") == base:
                return False
        return True

    def open_trade(self, signal: Dict, current_price: float):
        """Open a new trade"""
        if not self.can_open_trade(signal["base"]):
            return False

        notional = POSITION_SIZE_USD * LEVERAGE
        qty = notional / current_price
        stop = current_price * (1 + STOP_LOSS_PCT)  # SHORT: stop above entry
        tp = current_price * (1 - TAKE_PROFIT_PCT)  # SHORT: TP below entry

        trade = {
            "id": f"{signal['base']}_{int(time.time())}",
            "symbol": signal["symbol"],
            "base": signal["base"],
            "exchange": signal["exchange"],
            "direction": "SHORT",
            "entry": current_price,
            "qty": qty,
            "stop": stop,
            "tp": tp,
            "leverage": LEVERAGE,
            "margin": POSITION_SIZE_USD,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "status": "OPEN",
            "signal": signal
        }

        self.state["trades"].append(trade)
        self._save_state()
        return True

    def update_positions(self, get_price_func) -> List[Dict]:
        """Update positions and check for exits"""
        events = []
        open_trades = [t.copy() for t in self.state["trades"] if t.get("status") == "OPEN"]

        for trade in open_trades:
            current_price = get_price_func(trade["exchange"], trade["symbol"])
            if not current_price:
                continue

            # Calculate PnL (SHORT: profit when price goes down)
            pnl_pct = (trade["entry"] - current_price) / trade["entry"]
            pnl_usd = pnl_pct * trade["margin"] * LEVERAGE

            # Update trade in state
            for t in self.state["trades"]:
                if t.get("id") == trade.get("id"):
                    t["current_price"] = current_price
                    t["unrealized_pnl"] = pnl_usd
                    break

            # Check stop loss (SHORT: stop is above entry)
            if current_price >= trade["stop"]:
                self._close_trade(trade, current_price, "STOP LOSS", pnl_usd)
                events.append({"type": "STOP", "trade": trade, "pnl": pnl_usd})
                continue

            # Check take profit (SHORT: TP is below entry)
            if current_price <= trade["tp"]:
                self._close_trade(trade, current_price, "TAKE PROFIT", pnl_usd)
                events.append({"type": "TP", "trade": trade, "pnl": pnl_usd})
                continue

        self._save_state()
        return events

    def _close_trade(self, trade: Dict, exit_price: float, reason: str, pnl: float):
        """Close a trade"""
        trade["status"] = "CLOSED"
        trade["exit"] = exit_price
        trade["exit_at"] = datetime.now(timezone.utc).isoformat()
        trade["pnl"] = pnl
        trade["reason"] = reason

        # Update stats
        self.state["balance"] += pnl
        self.state["stats"]["realized_pnl"] += pnl
        self.state["stats"]["total_pnl"] += pnl
        self.state["stats"]["daily_pnl"] += pnl
        if pnl > 0:
            self.state["stats"]["wins"] += 1
        else:
            self.state["stats"]["losses"] += 1

        # Move to history
        self.state["history"].append(trade.copy())
        self.state["trades"] = [t for t in self.state["trades"] if t.get("id") != trade["id"]]

    def get_pnl_summary(self) -> Dict:
        """Get PnL summary"""
        open_trades = [t for t in self.state["trades"] if t.get("status") == "OPEN"]
        unrealized = sum(t.get("unrealized_pnl", 0) for t in open_trades)
        realized = self.state["stats"]["realized_pnl"]
        total = realized + unrealized

        return {
            "balance": self.state["balance"],
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
            "total_pnl": total,
            "daily_pnl": self.state["stats"]["daily_pnl"],
            "open_trades": len(open_trades),
            "wins": self.state["stats"]["wins"],
            "losses": self.state["stats"]["losses"]
        }


class ShortHunterBot:
    """Main bot orchestrator"""

    def __init__(self):
        self.ex_map: Dict[str, ccxt.Exchange] = {}
        self._init_exchanges()
        self.scanner = ShortHunterScanner(self.ex_map)
        self.paper_trader = PaperTrader()

    def _init_exchanges(self):
        """Initialize MEXC exchange - reliable data source"""
        try:
            # Use MEXC for reliable data access
            mexc_config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap'
                }
            }
            ex = ccxt.mexc(mexc_config)
            ex.load_markets()
            self.ex_map["mexc"] = ex
            logger.info(f"✅ MEXC ready ({len(ex.markets)} markets)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MEXC: {e}")

    def _live_px(self, exchange: str, symbol: str) -> Optional[float]:
        """Get live price for a symbol"""
        ex = self.ex_map.get(exchange)
        if not ex:
            return None
        # Clean symbol for MEXC
        clean_symbol = symbol.split(":")[0] if ":" in symbol else symbol
        try:
            t = ex.fetch_ticker(clean_symbol)
            px = float(t.get("last") or t.get("close") or 0)
            if px > 0:
                return px
        except Exception:
            pass
        return None

    def _check_breakdown_confirmation(self, signal: Dict, current_price: float) -> Tuple[bool, str]:
        """Check if price is actually breaking down (moving down) for better entry timing"""
        ex = self.ex_map.get(signal["exchange"])
        if not ex:
            return False, "No exchange"

        try:
            # Get recent OHLCV data to check momentum
            clean_symbol = signal["symbol"].split(":")[0] if ":" in signal["symbol"] else signal["symbol"]
            df = self.scanner._get_ohlcv_data(ex, clean_symbol, "15m", limit=20)
            if df is None or len(df) < 5:
                return False, "Insufficient data"

            entry_price = signal.get("entry_price") or signal.get("entry", current_price)

            # 1. Check if price is actually moving DOWN (momentum confirmation)
            recent_closes = df["close"].iloc[-5:].values
            price_moving_down = all(recent_closes[i] <= recent_closes[i-1] for i in range(1, len(recent_closes)))

            # 2. Check if price broke below a recent support/resistance level
            recent_high = df["high"].iloc[-10:].max()
            recent_low = df["low"].iloc[-10:].min()
            broke_below = current_price < recent_high * 0.995  # Broke below recent high by 0.5%

            # 3. Check volume on breakdown (should have volume when breaking down)
            recent_volume = df["volume"].iloc[-3:].mean()
            avg_volume = df["volume"].rolling(20).mean().iloc[-1] if len(df) >= 20 else recent_volume
            volume_confirmation = recent_volume >= avg_volume * 0.8  # At least average volume

            # 4. Check if we're getting a pullback entry (price pulled back to resistance, then breaking down)
            # For shorts: we want price to be near/at resistance, then break down
            percent_from_top = signal.get("percent_from_top", 100)
            near_top = percent_from_top < 2.0  # Within 2% of top

            # 5. RSI should be declining or at least not oversold yet
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            rsi_ok = current_rsi > 40  # Not oversold yet (room to fall)

            # Scoring system for breakdown confirmation
            confirmation_score = 0
            reasons = []

            # Price moving down (most important)
            if price_moving_down:
                confirmation_score += 40
                reasons.append("Price declining")
            elif recent_closes[-1] < recent_closes[-3]:  # At least lower than 3 bars ago
                confirmation_score += 25
                reasons.append("Price lower")

            # Broke below recent high
            if broke_below:
                confirmation_score += 30
                reasons.append("Broke below high")

            # Volume confirmation
            if volume_confirmation:
                confirmation_score += 15
                reasons.append("Volume OK")

            # Near top (good entry zone)
            if near_top:
                confirmation_score += 10
                reasons.append("Near top")

            # RSI not oversold
            if rsi_ok:
                confirmation_score += 5
                reasons.append("RSI OK")

            # Require at least 50 points for confirmation (price moving down is key)
            confirmed = confirmation_score >= 50

            reason_str = " + ".join(reasons) if reasons else "No confirmation"
            return confirmed, reason_str

        except Exception as e:
            logger.debug(f"Error checking breakdown confirmation: {e}")
            return False, f"Error: {str(e)}"

    def _post_discord(self, embeds: List[Dict], ping: bool = False):
        """Post to Discord - optional ping"""
        if not DISCORD_WEBHOOK:
            logger.warning("No Discord webhook configured")
            return False

        try:
            payload = {"embeds": embeds}
            if ping:
                # Use regular ping notification (not @here)
                payload["content"] = "🔔 **TRADE OPENED** 🔔"
            r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"📤 Posted {len(embeds)} embeds to Discord{' with ping' if ping else ''}")
            return True
        except Exception as e:
            logger.error(f"Discord post error: {e}")
            return False

    def _create_short_card(self, signal: Dict) -> Dict:
        """Create Discord embed card for SHORT signal"""
        base = signal.get("base", "N/A")
        entry = signal.get("entry", 0)
        confidence = signal.get("confidence", 0)
        dev_level = signal.get("deviation_level", 0)
        dev_source = signal.get("deviation_source", "").upper()
        percent_from_top = signal.get("percent_from_top", 0)
        reasons = signal.get("reasons", "")
        exchange = signal.get("exchange", "").upper()
        timeframe = signal.get("timeframe", "")
        link = tv_link(signal["symbol"], signal["exchange"])

        # Grade based on deviation
        grade = "A++" if dev_level >= 3 else "A+" if dev_level >= 2 else "A"

        desc = [
            f"**🔴 {base} SHORT** {grade}",
            f"**Entry:** ${entry:,.6f}",
            f"**Exchange:** {exchange}",
            f"**Timeframe:** {timeframe}",
            f"**Confidence:** {confidence}/10",
            f"**Deviation:** {dev_level}σ {dev_source} VWAP",
            f"**From Top:** {percent_from_top:.2f}%",
            f"**Chart:** [TradingView]({link})",
            f"**Analysis:** {reasons}"
        ]

        if signal.get("rsi"):
            desc.append(f"**RSI:** {signal['rsi']:.1f}")
        if signal.get("volume_ratio"):
            desc.append(f"**Volume:** {signal['volume_ratio']:.1f}x avg")

        color = 0x8E44AD  # Purple for shorts

        return {
            "title": f"🎯 SHORT Signal — {base}",
            "description": "\n".join(desc),
            "color": color,
            "footer": {"text": f"Short Hunter Bot • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_short_batch_card(self, signals: List[Dict]) -> Optional[Dict]:
        """Create a single purple card aggregating up to 3 short signals with better spacing"""
        if not signals:
            return None

        blocks = []
        for s in signals:
            base = s.get("base", "N/A")
            entry = s.get("entry", 0)
            confidence = s.get("confidence", 0)
            percent_from_top = s.get("percent_from_top", 0)
            dev_level = s.get("deviation_level", 0)
            dev_source = s.get("deviation_source", "N/A").upper()
            reasons = s.get("reasons", "Near top")
            rsi = s.get("rsi")
            volume_ratio = s.get("volume_ratio")
            link = tv_link(s["symbol"], s["exchange"])

            # Format like screenshot: clean, spaced out, easy to read
            block_lines = [
                f"**{base}:**",
                f"**Entry:** ${entry:,.6f}",
                f"**Conf:** {confidence}/10",
                f"**{percent_from_top:.1f}% from top**",
                f"**Dev:** {dev_level}σ {dev_source}",
                f"**Why:** {reasons}",
                f"[Chart]({link})"
            ]

            blocks.append("\n".join(block_lines))

        # Add spacing between signals (double newline between each)
        return {
            "title": "SHORT Signals (Top 3)",
            "description": "\n\n".join(blocks),
            "color": 0x8E44AD,  # Purple
            "footer": {"text": f"Short Hunter Bot • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"}
        }

    def _create_sfp_batch_card(self, alerts: List[Dict]) -> Optional[Dict]:
        """Create a single yellow card aggregating SFP alerts with better spacing"""
        if not alerts:
            return None
        blocks = []
        for a in alerts:
            base = a.get("base", "N/A")
            current_price = a.get("current_price", 0)
            pivot_high = a.get("pivot_high", 0)
            score = a.get("score", 0)
            rsi = a.get("rsi", 0)
            volume_ratio = a.get("volume_ratio", 1.0)
            link = tv_link(a["symbol"], a["exchange"])
            dist = ((current_price - pivot_high) / pivot_high) * 100 if pivot_high else 0

            block_lines = [
                f"**{base}:**",
                f"**Price:** ${current_price:,.6f} ({dist:+.2f}% from pivot)",
                f"**Score:** {score}",
                f"**RSI:** {rsi:.1f}",
                f"**Volume:** {volume_ratio:.1f}x",
                f"[Chart]({link})"
            ]
            blocks.append("\n".join(block_lines))

        return {
            "title": "⚠️ SFP Alerts (Top 3)",
            "description": "\n\n".join(blocks),
            "color": 0xFFFF00,
            "footer": {"text": "Swing Failure Pattern • Reversal Alerts"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_bearish_batch_card(self, alerts: List[Dict]) -> Optional[Dict]:
        """Create a single red card aggregating high-alert bearish patterns with better spacing"""
        if not alerts:
            return None
        blocks = []
        for a in alerts:
            base = a.get("base", "N/A")
            pattern = a.get("pattern_name", "Bearish")
            score = a.get("score", 0)
            current_price = a.get("current_price", 0)
            rsi = a.get("rsi", 0)
            volume_ratio = a.get("volume_ratio", 1.0)
            link = tv_link(a["symbol"], a["exchange"])

            block_lines = [
                f"**{base}:**",
                f"**Pattern:** {pattern}",
                f"**Price:** ${current_price:,.6f}",
                f"**Score:** {score}",
                f"**RSI:** {rsi:.1f}",
                f"**Volume:** {volume_ratio:.1f}x",
                f"[Chart]({link})"
            ]
            blocks.append("\n".join(block_lines))

        return {
            "title": "🔴 High-Alert Bearish Patterns",
            "description": "\n\n".join(blocks),
            "color": 0xFF0000,
            "footer": {"text": "High-End Short Opportunities"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_trade_closed_batch_card(self, events: List[Dict]) -> Optional[Dict]:
        """Create a single red card aggregating stop/tp exits"""
        if not events:
            return None
        lines = []
        for ev in events:
            trade = ev["trade"]
            pnl = ev["pnl"]
            base = trade["base"]
            entry = trade["entry"]
            exit_price = trade["exit"]
            reason = trade["reason"]
            pnl_pct = (pnl / (trade["margin"] * LEVERAGE)) * 100
            lines.append(
                f"**{base}** • {reason} • Entry ${entry:,.6f} → Exit ${exit_price:,.6f} • "
                f"PnL ${pnl:+.2f} ({pnl_pct:+.2f}%)"
            )
        return {
            "title": "🛑 Exits / Stops",
            "description": "\n".join(lines),
            "color": 0xFF0000,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_watchlist_card(self, items: List[Dict]) -> Optional[Dict]:
        """
        Watchlist output has been disabled per user request.

        This function now always returns None so no watchlist embed is ever posted,
        even if this helper is called.
        """
        return None

    def _create_sfp_alert_card(self, alert: Dict) -> Dict:
        """Create yellow SFP alert card"""
        base = alert.get("base", "N/A")
        pivot_high = alert.get("pivot_high", 0)
        current_price = alert.get("current_price", 0)
        reversal_strength = alert.get("reversal_strength", 0)
        score = alert.get("score", 0)
        rsi = alert.get("rsi", 0)
        volume_ratio = alert.get("volume_ratio", 1.0)
        bars_since = alert.get("bars_since_reversal", alert.get("bars_since_break", 0))
        link = tv_link(alert["symbol"], alert["exchange"])

        # Calculate distance from pivot
        distance_from_pivot = ((current_price - pivot_high) / pivot_high) * 100

        desc = [
            f"**⚠️ {base} BEARISH SFP ALERT**",
            f"**Pivot High:** ${pivot_high:,.6f}",
            f"**Current:** ${current_price:,.6f} ({distance_from_pivot:+.2f}%)",
            f"**Reversal Strength:** {reversal_strength:.2f}%",
            f"**SFP Score:** {score}/120",
            f"**RSI:** {rsi:.1f}",
            f"**Volume:** {volume_ratio:.1f}x avg",
            f"**Bars Since Break:** {bars_since}",
            f"**Chart:** [TradingView]({link})",
            "",
            "⚠️ **Potential reversal trade setup**"
        ]

        return {
            "title": f"⚠️ SFP Alert — {base}",
            "description": "\n".join(desc),
            "color": 0xFFFF00,  # Yellow
            "footer": {"text": "Swing Failure Pattern • Reversal Alert"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_bearish_pattern_card(self, alert: Dict) -> Dict:
        """Create red high alert card for bearish patterns (currently Topping Breakdown only)"""
        base = alert.get("base", "N/A")
        pattern_name = alert.get("pattern_name", "Bearish Pattern")
        pattern_type = alert.get("pattern", "")
        score = alert.get("score", 0)
        current_price = alert.get("current_price", 0)
        rsi = alert.get("rsi", 0)
        volume_ratio = alert.get("volume_ratio", 1.0)
        link = tv_link(alert["symbol"], alert["exchange"])

        desc = [
            f"**🔴 {base} {pattern_name.upper()} ALERT**",
            f"**Pattern:** {pattern_name}",
            f"**Current Price:** ${current_price:,.6f}",
            f"**Pattern Score:** {score}/120",
            f"**RSI:** {rsi:.1f}",
            f"**Volume:** {volume_ratio:.1f}x avg",
        ]

        # Add pattern-specific details
        if pattern_type == "TOPPING_BREAKDOWN":
            high_price = alert.get("high_price", 0)
            decline_pct = alert.get("decline_pct", 0)
            bars_since = alert.get("bars_since_high", 0)

            desc.append(f"**High Price:** ${high_price:,.6f}")
            desc.append(f"**Decline from High:** {decline_pct:.2f}%")
            desc.append(f"**Bars Since High:** {bars_since}")
            desc.append("")
            desc.append("🔴 **HIGH-END SHORT OPPORTUNITY**")
            desc.append("Topping pattern with breakdown - Potential downside runner")

        desc.append(f"**Chart:** [TradingView]({link})")

        return {
            "title": f"🔴 HIGH ALERT — {base} {pattern_name}",
            "description": "\n".join(desc),
            "color": 0xFF0000,  # Red
            "footer": {"text": "Bearish Reversal Pattern • High-End Short Opportunity"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_trade_opened_card(self, trade: Dict) -> Dict:
        """Create card for trade opened"""
        base = trade["base"]
        entry = trade["entry"]
        stop = trade["stop"]
        tp = trade["tp"]
        link = tv_link(trade["symbol"], trade["exchange"])

        return {
            "title": f"🟣 TRADE OPENED — {base} SHORT",
            "description": (
                f"**Entry:** ${entry:,.6f}\n"
                f"**Stop:** ${stop:,.6f} (+{STOP_LOSS_PCT*100:.1f}%)\n"
                f"**TP:** ${tp:,.6f} (-{TAKE_PROFIT_PCT*100:.1f}%)\n"
                f"**Size:** ${POSITION_SIZE_USD} margin ({LEVERAGE}x)\n"
                f"**Chart:** [TradingView]({link})"
            ),
            "color": 0xFF69B4,  # Pink for entries
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_trade_closed_card(self, event: Dict) -> Dict:
        """Create card for trade closed"""
        trade = event["trade"]
        pnl = event["pnl"]
        base = trade["base"]
        entry = trade["entry"]
        exit_price = trade["exit"]
        reason = trade["reason"]
        pnl_pct = (pnl / (trade["margin"] * LEVERAGE)) * 100

        is_stop = "STOP" in reason.upper()
        color = 0xFF0000 if is_stop else (0x00FF00 if pnl > 0 else 0xFF0000)
        emoji = "🛑" if is_stop else ("✅" if pnl > 0 else "❌")

        return {
            "title": f"{emoji} TRADE CLOSED — {base} SHORT",
            "description": (
                f"**Reason:** {reason}\n"
                f"**Entry:** ${entry:,.6f}\n"
                f"**Exit:** ${exit_price:,.6f}\n"
                f"**PnL:** ${pnl:+.2f} ({pnl_pct:+.2f}%)\n"
                f"**Duration:** {self._format_duration(trade['opened_at'], trade['exit_at'])}"
            ),
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _create_pnl_update_card(self, pnl_data: Dict) -> Dict:
        """Create PnL update card"""
        return {
            "title": "💰 PnL Update",
            "description": (
                f"**Balance:** ${pnl_data['balance']:,.2f}\n"
                f"**Realized PnL:** ${pnl_data['realized_pnl']:+.2f}\n"
                f"**Unrealized PnL:** ${pnl_data['unrealized_pnl']:+.2f}\n"
                f"**Total PnL:** ${pnl_data['total_pnl']:+.2f}\n"
                f"**Daily PnL:** ${pnl_data['daily_pnl']:+.2f}\n"
                f"**Open Trades:** {pnl_data['open_trades']}/{MAX_OPEN_TRADES}\n"
                f"**W/L:** {pnl_data['wins']}W / {pnl_data['losses']}L"
            ),
            "color": 0x00FF00 if pnl_data['total_pnl'] > 0 else 0xFF0000,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _format_duration(self, start: str, end: str) -> str:
        """Format duration between two timestamps"""
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            delta = end_dt - start_dt
            hours = int(delta.total_seconds() / 3600)
            minutes = int((delta.total_seconds() % 3600) / 60)
            return f"{hours}h {minutes}m"
        except:
            return "N/A"

    def _create_all_trades_card(self) -> Optional[Dict]:
        """Create a single card showing all trades (open + closed) with reasons and PnL"""
        open_trades = [t for t in self.paper_trader.state.get("trades", []) if t.get("status") == "OPEN"]
        closed_trades = self.paper_trader.state.get("history", [])

        if not open_trades and not closed_trades:
            return {
                "title": "📊 All Trades",
                "description": "No trades yet.",
                "color": 0x8E44AD
            }

        lines = []

        # Update open trades with current prices and PnL
        for trade in open_trades:
            current_price = self._live_px(trade["exchange"], trade["symbol"])
            if current_price:
                pnl_pct = (trade["entry"] - current_price) / trade["entry"]
                pnl_usd = pnl_pct * trade["margin"] * LEVERAGE
            else:
                pnl_usd = trade.get("unrealized_pnl", 0)
                pnl_pct = (pnl_usd / (trade["margin"] * LEVERAGE)) * 100 if trade["margin"] > 0 else 0

            base = trade.get("base", "N/A")
            entry = trade.get("entry", 0)
            signal = trade.get("signal", {})
            reasons = signal.get("reasons", "Near top + Resistance")

            lines.append(f"**🟢 {base} SHORT (OPEN)**")
            lines.append(f"Entry: ${entry:,.6f}")
            if current_price:
                lines.append(f"Current: ${current_price:,.6f}")
            lines.append(f"PnL: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
            lines.append(f"Why: {reasons}")
            lines.append("")  # Blank line for spacing

        # Add closed trades
        for trade in closed_trades[-20:]:  # Last 20 closed trades
            base = trade.get("base", "N/A")
            entry = trade.get("entry", 0)
            exit_price = trade.get("exit", 0)
            pnl = trade.get("pnl", 0)
            reason = trade.get("reason", "CLOSED")
            signal = trade.get("signal", {})
            reasons = signal.get("reasons", "Near top + Resistance")

            pnl_pct = (pnl / (trade.get("margin", POSITION_SIZE_USD) * LEVERAGE)) * 100 if trade.get("margin", 0) > 0 else 0
            emoji = "✅" if pnl > 0 else "❌"

            lines.append(f"**{emoji} {base} SHORT (CLOSED)**")
            lines.append(f"Entry: ${entry:,.6f} → Exit: ${exit_price:,.6f}")
            lines.append(f"PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%) • {reason}")
            lines.append(f"Why: {reasons}")
            lines.append("")  # Blank line for spacing

        # Add summary at the end
        pnl_data = self.paper_trader.get_pnl_summary()
        lines.append("**━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━**")
        lines.append(f"**Total PnL:** ${pnl_data['total_pnl']:+.2f}")
        lines.append(f"**Realized:** ${pnl_data['realized_pnl']:+.2f} • **Unrealized:** ${pnl_data['unrealized_pnl']:+.2f}")
        lines.append(f"**W/L:** {pnl_data['wins']}W / {pnl_data['losses']}L")

        return {
            "title": "📊 All Trades — Open & Closed",
            "description": "\n".join(lines),
            "color": 0x8E44AD,  # Purple
            "footer": {"text": f"Short Hunter Bot • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def ping_all_trades(self):
        """Post all trades card to Discord"""
        # Update positions first to get latest PnL
        self.paper_trader.update_positions(self._live_px)
        card = self._create_all_trades_card()
        if card:
            self._post_discord([card], ping=False)
            logger.info("📊 Posted all trades card")

    def _should_post_pnl_update(self) -> bool:
        """Check if we should post PnL update (4 times per day)"""
        current_hour = datetime.now(timezone.utc).hour
        if current_hour in PNL_UPDATE_INTERVALS:
            if self.paper_trader.last_pnl_update_hour != current_hour:
                self.paper_trader.last_pnl_update_hour = current_hour
                return True
        return False

    def run_scan(self):
        """Run one scan cycle"""
        logger.info("🚀 Starting SHORT scan...")

        # Update existing positions
        events = self.paper_trader.update_positions(self._live_px)

        # Post trade events (no ping)
        if events:
            exit_events = [e for e in events if e["type"] in ["STOP", "TP"]]
            if exit_events:
                batch_card = self._create_trade_closed_batch_card(exit_events)
                if batch_card:
                    self._post_discord([batch_card])
                    logger.info(f"📢 Posted exits/stops batch ({len(exit_events)} events)")

        # Scan for new opportunities
        shorts = self.scanner.scan_for_shorts()

        # Scan for SFP alerts (top 3 most probable)
        sfp_alerts = self.scanner.scan_for_sfp_alerts()

        # Scan for bearish patterns (Topping Breakdown) - high-end shorts
        bearish_patterns = self.scanner.scan_for_bearish_patterns()

        # FINAL STRICT FILTER: Remove any coins not in allowed list (safety net)
        def filter_allowed_coins(items: List[Dict]) -> List[Dict]:
            """Filter out any items not in allowed coins list"""
            filtered = []
            for item in items:
                base = item.get("base", "").upper()
                if base in self.scanner.ALLOWED_COINS:
                    filtered.append(item)
                else:
                    logger.warning(f"🚫 FILTERED OUT: {base} (not in allowed list)")
            return filtered

        # Apply final filter to all results
        shorts = filter_allowed_coins(shorts)
        sfp_alerts = filter_allowed_coins(sfp_alerts)
        bearish_patterns = filter_allowed_coins(bearish_patterns)

        logger.info(f"✅ After filtering: {len(shorts)} shorts, {len(sfp_alerts)} SFP alerts, {len(bearish_patterns)} bearish patterns")

        # Check pending signals and open trades when price reaches entry
        opened_trades = []
        pending_signals = self.paper_trader.state.get("pending_signals", [])
        current_time = datetime.now(timezone.utc)

        # Check if any pending signals are ready to enter
        for signal in pending_signals[:]:
            # FINAL CHECK: Verify base is in allowed list
            base = signal.get("base", "").upper()
            if base not in self.scanner.ALLOWED_COINS:
                logger.warning(f"🚫 Removing invalid pending signal: {base} (not in allowed list)")
                pending_signals.remove(signal)
                continue

            current_price = self._live_px(signal["exchange"], signal["symbol"])
            if not current_price:
                continue

            # Get entry price and signal creation time
            entry = signal.get("entry_price") or signal.get("entry")
            if not entry:
                continue

            # Get signal age (time since creation)
            created_at_str = signal.get("created_at", current_time.isoformat())
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                signal_age_seconds = (current_time - created_at).total_seconds()
            except:
                signal_age_seconds = 0

            # REQUIREMENTS FOR OPENING TRADE (wait for actual breakdown)
            # 1. Price must be near target entry (within 2% for pullback entries, or slightly below for breakdown entries)
            # 2. MOST IMPORTANT: Price must be actually moving DOWN (breakdown confirmation)
            price_diff_pct = abs(current_price - entry) / entry

            # Check for breakdown confirmation (price actually moving down)
            breakdown_confirmed, breakdown_reason = self._check_breakdown_confirmation(signal, current_price)

            # Entry conditions:
            # - If breakdown confirmed: can enter slightly below entry (breakdown entry)
            # - If no breakdown yet: must be at/above entry (waiting for pullback)
            if breakdown_confirmed:
                # Breakdown confirmed: can enter if price is within 2% of entry (above or slightly below)
                price_near_entry = price_diff_pct <= 0.02
            else:
                # No breakdown yet: must be at/above entry (waiting for pullback to resistance)
                price_near_entry = current_price >= entry * 0.99 and price_diff_pct <= 0.01

            # ENHANCED ENTRY LOGIC: Only enter when price is actually breaking down
            if price_near_entry and breakdown_confirmed:
                if self.paper_trader.can_open_trade(signal["base"]):
                    if self.paper_trader.open_trade(signal, current_price):
                        new_trade = self.paper_trader.state["trades"][-1]
                        opened_trades.append(new_trade)
                        logger.info(f"📈 Opened {signal['base']} SHORT at ${current_price:,.6f} (entry: ${entry:,.6f}, breakdown: {breakdown_reason})")
                        # Post trade opened notification IMMEDIATELY with ping
                        trade_embed = self._create_trade_opened_card(new_trade)
                        self._post_discord([trade_embed], ping=True)
                        logger.info(f"🔔 Posted trade opened notification for {signal['base']} with ping")
                        pending_signals.remove(signal)
                else:
                    pending_signals.remove(signal)
            elif price_near_entry and not breakdown_confirmed:
                # Price is near entry but not breaking down yet - wait
                logger.debug(f"⏳ {signal['base']} near entry ${entry:,.6f} but waiting for breakdown confirmation (current: ${current_price:,.6f}, reason: {breakdown_reason})")
            # Remove old signals (older than 4 hours)
            elif signal_age_seconds > 14400:
                logger.info(f"⏰ Removing expired signal: {signal['base']} (age: {signal_age_seconds/3600:.1f}h)")
                pending_signals.remove(signal)

        # Add new signals to pending (don't auto-open) - POST SIGNALS TO DISCORD
        new_signals = []
        for short in shorts[:MAX_SHORTS]:
            # FINAL CHECK: Verify base is in allowed list
            base = short.get("base", "").upper()
            if base not in self.scanner.ALLOWED_COINS:
                logger.warning(f"🚫 Rejected signal for {base} - not in allowed list!")
                continue

            # Check if already pending or already open
            already_pending = any(s.get("base") == short["base"] for s in pending_signals)
            already_open = any(t.get("base") == short["base"] and t.get("status") == "OPEN" for t in self.paper_trader.state["trades"])

            if not already_pending and not already_open:
                signal_entry = {
                    **short,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "entry_price": short["entry"]  # Target entry price
                }
                pending_signals.append(signal_entry)
                new_signals.append(short)
                logger.info(f"📋 Added {short['base']} to pending signals (entry: ${short['entry']:,.6f})")

        # Post new signals to Discord immediately
        if new_signals:
            batch_card = self._create_short_batch_card(new_signals[:3])
            embeds_to_post = [batch_card] if batch_card else []
            # Fallback to individual cards if batch fails
            if not embeds_to_post:
                embeds_to_post = [self._create_short_card(s) for s in new_signals]
            self._post_discord(embeds_to_post)
            logger.info(f"📢 Posted {len(new_signals)} new SHORT signals to Discord (batched)")

        # Save pending signals
        self.paper_trader.state["pending_signals"] = pending_signals
        self.paper_trader._save_state()

        # Note: Trade opened notifications are posted immediately above when trades are opened

        # Post PnL update 4 times per day
        if self._should_post_pnl_update():
            pnl_data = self.paper_trader.get_pnl_summary()
            pnl_embed = self._create_pnl_update_card(pnl_data)
            self._post_discord([pnl_embed])
            logger.info("📊 Posted PnL update")

        # Regular scan results summary (always post summary)
        embeds = []

        # Summary
        embeds.append({
            "title": "📊 Short Hunter Bot - Scan Complete",
            "description": (
                f"**Bot:** Short Hunter\n"
                f"**Exchange:** MEXC\n"
                f"**Universe:** {len(self.scanner.watchlist)} futures pairs\n"
                f"**Shorts Found:** {len(shorts)}\n"
                f"**New Signals:** {len(new_signals)}\n"
                f"**SFP Alerts:** {len(sfp_alerts)}\n"
                f"**Bearish Patterns:** {len(bearish_patterns)} (High-End Shorts)\n"
                f"**Open Trades:** {len([t for t in self.paper_trader.state['trades'] if t.get('status') == 'OPEN'])}/{MAX_OPEN_TRADES}\n"
                f"**Pending Signals:** {len(pending_signals)}"
            ),
            "color": 0x8E44AD  # Purple
        })

        # Bearish Patterns (red high alert cards) - post first (highest priority)
        if bearish_patterns:
            batch = self._create_bearish_batch_card(bearish_patterns)
            if batch:
                embeds.append(batch)
            logger.info(f"🔴 Posted {len(bearish_patterns)} bearish pattern alerts (HIGH-END SHORTS) batched")

        # SFP Alerts (yellow cards) - post after bearish patterns
        if sfp_alerts:
            batch = self._create_sfp_batch_card(sfp_alerts)
            if batch:
                embeds.append(batch)
            logger.info(f"⚠️ Posted {len(sfp_alerts)} SFP alerts batched")

        # Post summary (signals already posted above if new)
        if embeds:
            self._post_discord(embeds)
            logger.info(f"📤 Posted scan summary to Discord")

    def run_continuous(self):
        """Run continuous scanning"""
        logger.info(f"🔄 Continuous mode — scanning every {SCAN_INTERVAL_SEC // 60} minutes")
        while True:
            try:
                self.run_scan()
                logger.info(f"⏰ Next scan in {SCAN_INTERVAL_SEC // 60} minutes...")
                time.sleep(SCAN_INTERVAL_SEC)
            except KeyboardInterrupt:
                logger.info("🛑 Stopping")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}", exc_info=True)
                logger.info(f"⏰ Retrying in {SCAN_INTERVAL_SEC // 60} minutes...")
                time.sleep(SCAN_INTERVAL_SEC)  # Wait full interval even on error


if __name__ == "__main__":
    import sys
    bot = ShortHunterBot()
    if len(sys.argv) > 1:
        if sys.argv[1] == "continuous":
            bot.run_continuous()
        elif sys.argv[1] == "trades":
            bot.ping_all_trades()
        else:
            bot.run_scan()
    else:
        bot.run_scan()
