#!/usr/bin/env python3
"""
PivotX Scanner Bot
- Scans for pivots on 5m, 15m, and 1H timeframes
- Focuses on BTC, SOL, SUI and top 100 cryptos
- Detects pullbacks to pivot zones for scalping opportunities
- Maintains watchlist of 3-4 coins with best setups
"""

import os
import json
import time
import logging
import requests
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pivotx_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PivotXScanner")

# Discord webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1450009873734434867/2-sSMgoMU0mwWoZfe-RVX6Vamp7NNjPK74lSOwYi2nOqP9N_6YLFJe6bGOttz1Eydjie"

# Configuration
SCAN_INTERVAL_SEC = 30 * 60  # 30 minutes
TIMEFRAMES = ["5m", "15m", "1h", "8h", "12h", "1d"]  # All timeframes including trend change timeframes
PRIORITY_COINS = ["BTCUSDT", "SOLUSDT", "SUIUSDT"]  # Only send alerts for these
ALERT_COINS = ["BTCUSDT", "SOLUSDT", "SUIUSDT"]  # Coins that trigger alerts
TREND_CHANGE_TIMEFRAMES = ["8h", "12h", "1d"]  # Super alert timeframes for trend changes

# Exchange configuration - use Coinbase first, fallback to Kraken
USE_EXCHANGE = "coinbase"  # "coinbase" or "kraken"

# Pivot detection parameters
ATR_MULTIPLIER = 0.5
ATR_PERIOD = 14
VOLUME_THRESHOLD = 1.5
ATR_CONFIRM_MULT = 0.2

# Watchlist settings
MAX_WATCHLIST_SIZE = 4  # 3-4 coins in watchlist
WATCHLIST_FILE = "pivotx_watchlist.json"


@dataclass
class Pivot:
    """Pivot point data"""
    symbol: str
    timeframe: str
    pivot_type: str  # "HIGH" or "LOW"
    price: float
    bar_index: int
    timestamp: datetime
    atr: float
    confirmed: bool
    pullback_distance: float = 0.0  # Distance from current price
    setup_quality: str = ""  # "A+", "A", "B"


@dataclass
class WatchlistEntry:
    """Watchlist entry"""
    symbol: str
    pivot: Pivot
    current_price: float
    distance_to_pivot: float
    setup_type: str  # "PULLBACK" or "UPCOMING"
    score: float


class PivotXScanner:
    def __init__(self):
        self.watchlist: List[WatchlistEntry] = []
        self.detected_pivots: Dict[str, List[Pivot]] = defaultdict(list)
        self.last_scan_time = {}
        self.sent_cards: set = set()  # Track sent cards to avoid duplicates

        # Initialize exchange
        try:
            if USE_EXCHANGE == "coinbase":
                self.exchange = ccxt.coinbase({
                    'apiKey': '',
                    'secret': '',
                    'enableRateLimit': True,
                    'options': {'adjustForTimeDifference': True}
                })
            else:  # kraken
                self.exchange = ccxt.kraken({
                    'apiKey': '',
                    'secret': '',
                    'enableRateLimit': True
                })
            logger.info(f"Initialized {USE_EXCHANGE} exchange")
        except Exception as e:
            logger.error(f"Error initializing exchange: {e}")
            # Try Kraken as fallback
            try:
                logger.info("Trying Kraken as fallback...")
                self.exchange = ccxt.kraken({
                    'apiKey': '',
                    'secret': '',
                    'enableRateLimit': True
                })
                logger.info("Initialized Kraken exchange as fallback")
            except Exception as e2:
                logger.error(f"Error initializing Kraken fallback: {e2}")
                self.exchange = None

    def map_symbol_for_exchange(self, symbol: str) -> str:
        """Map symbol format for exchange"""
        # Remove USDT suffix and format for exchange
        base = symbol.replace("USDT", "")

        if USE_EXCHANGE == "coinbase":
            # Coinbase uses BTC-USD format
            return f"{base}-USD"
        else:  # kraken
            # Kraken uses BTC/USD format
            return f"{base}/USD"

    def fetch_klines(self, symbol: str, interval: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch klines from Coinbase or Kraken using ccxt"""
        if self.exchange is None:
            logger.error("Exchange not initialized")
            return None

        try:
            # Map symbol for exchange
            exchange_symbol = self.map_symbol_for_exchange(symbol)

            # Map timeframe to exchange format
            timeframe_map = {
                "5m": "5m",
                "15m": "15m",
                "1h": "1h",
                "8h": "8h",
                "12h": "12h",
                "1d": "1d"
            }
            tf = timeframe_map.get(interval, interval)

            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(exchange_symbol, tf, limit=limit)

            if not ohlcv or len(ohlcv) == 0:
                logger.warning(f"No data returned for {exchange_symbol} {tf}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['open_time'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['close_time'] = df['open_time']  # Approximate
            df = df.drop('timestamp', axis=1)

            # Ensure proper types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df

        except ccxt.BaseError as e:
            logger.error(f"Exchange error fetching {symbol} {interval}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol} {interval}: {e}")
            return None

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        return true_range.rolling(window=period).mean()

    def calculate_pivot_strength(self, atr: float, mintick: float = 0.01) -> int:
        """Calculate dynamic pivot strength based on ATR"""
        pivot_strength_raw = max(2, round(atr / mintick * ATR_MULTIPLIER))
        # Cap based on timeframe (we'll adjust in detection)
        return min(pivot_strength_raw, 50)

    def detect_pivots(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[Pivot]:
        """Detect pivot highs and lows"""
        if df is None or len(df) < 50:
            return []

        pivots = []

        # Calculate ATR
        atr_series = self.calculate_atr(df, ATR_PERIOD)
        current_atr = atr_series.iloc[-1] if not atr_series.empty else 0

        if current_atr == 0:
            return []

        # Determine pivot strength based on timeframe
        if timeframe == "5m":
            min_strength = 5
            max_strength = 15
        elif timeframe == "15m":
            min_strength = 3
            max_strength = 20
        elif timeframe == "1h":
            min_strength = 2
            max_strength = 30
        elif timeframe in ["8h", "12h"]:
            min_strength = 2
            max_strength = 20
        elif timeframe == "1d":
            min_strength = 2
            max_strength = 15
        else:
            min_strength = 2
            max_strength = 30

        pivot_strength = max(min_strength, min(self.calculate_pivot_strength(current_atr), max_strength))

        # Need enough bars
        if len(df) < pivot_strength * 2 + 1:
            return []

        # Detect pivot highs
        for i in range(pivot_strength, len(df) - pivot_strength):
            high_val = df.iloc[i]['high']
            is_pivot_high = True

            # Check left and right sides
            for j in range(1, pivot_strength + 1):
                if df.iloc[i - j]['high'] >= high_val or df.iloc[i + j]['high'] >= high_val:
                    is_pivot_high = False
                    break

            if is_pivot_high:
                # ATR confirmation
                current_price = df.iloc[-1]['close']
                atr_confirmed = current_price < high_val - (current_atr * ATR_CONFIRM_MULT)

                # Include recent pivots (more bars for higher timeframes)
                recent_bars = 200 if timeframe in TREND_CHANGE_TIMEFRAMES else 100
                if i >= len(df) - recent_bars:
                    # Determine quality based on timeframe
                    if timeframe in TREND_CHANGE_TIMEFRAMES:
                        quality = "TREND CHANGE"
                    elif timeframe == "1h":
                        quality = "A+"
                    elif timeframe == "15m":
                        quality = "A"
                    else:
                        quality = "B"

                    pivot = Pivot(
                        symbol=symbol,
                        timeframe=timeframe,
                        pivot_type="HIGH",
                        price=high_val,
                        bar_index=i,
                        timestamp=df.iloc[i]['open_time'],
                        atr=current_atr,
                        confirmed=atr_confirmed,
                        setup_quality=quality
                    )
                    pivots.append(pivot)

        # Detect pivot lows
        for i in range(pivot_strength, len(df) - pivot_strength):
            low_val = df.iloc[i]['low']
            is_pivot_low = True

            # Check left and right sides
            for j in range(1, pivot_strength + 1):
                if df.iloc[i - j]['low'] <= low_val or df.iloc[i + j]['low'] <= low_val:
                    is_pivot_low = False
                    break

            if is_pivot_low:
                # ATR confirmation
                current_price = df.iloc[-1]['close']
                atr_confirmed = current_price > low_val + (current_atr * ATR_CONFIRM_MULT)

                # Include recent pivots (more bars for higher timeframes)
                recent_bars = 200 if timeframe in TREND_CHANGE_TIMEFRAMES else 100
                if i >= len(df) - recent_bars:
                    # Determine quality based on timeframe
                    if timeframe in TREND_CHANGE_TIMEFRAMES:
                        quality = "TREND CHANGE"
                    elif timeframe == "1h":
                        quality = "A+"
                    elif timeframe == "15m":
                        quality = "A"
                    else:
                        quality = "B"

                    pivot = Pivot(
                        symbol=symbol,
                        timeframe=timeframe,
                        pivot_type="LOW",
                        price=low_val,
                        bar_index=i,
                        timestamp=df.iloc[i]['open_time'],
                        atr=current_atr,
                        confirmed=atr_confirmed,
                        setup_quality=quality
                    )
                    pivots.append(pivot)

        return pivots

    def check_pullback(self, df: pd.DataFrame, pivot: Pivot) -> Tuple[bool, float]:
        """Check if price is pulling back to pivot zone"""
        if df is None or len(df) == 0:
            return False, 0.0

        current_price = df.iloc[-1]['close']
        pivot_price = pivot.price
        atr = pivot.atr

        # Define pivot zone (±30% of ATR)
        zone_top = pivot_price + (atr * 0.3)
        zone_bottom = pivot_price - (atr * 0.3)

        # Check if current price is near the pivot zone
        in_zone = zone_bottom <= current_price <= zone_top

        # Calculate distance to pivot
        if pivot.pivot_type == "HIGH":
            distance_pct = ((current_price - pivot_price) / pivot_price) * 100
            # For pivot high, we want price below it (negative distance)
            pullback = distance_pct < 2.0  # Within 2% below pivot high
        else:  # LOW
            distance_pct = ((current_price - pivot_price) / pivot_price) * 100
            # For pivot low, we want price above it (positive distance)
            pullback = distance_pct < 2.0  # Within 2% above pivot low

        return (in_zone or pullback), abs(distance_pct)

    def get_top_100_coins(self) -> List[str]:
        """Get top crypto symbols from exchange"""
        if self.exchange is None:
            # Fallback to common coins
            return [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
                "ADAUSDT", "AVAXUSDT", "SUIUSDT", "APTUSDT", "NEARUSDT", "OPUSDT",
                "ARBUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT"
            ]

        try:
            # Fetch markets from exchange
            markets = self.exchange.load_markets()

            # Filter for USD pairs and get symbols
            usd_pairs = []
            for market_id, market in markets.items():
                if market['quote'] == 'USD' and market['active']:
                    # Convert back to USDT format for consistency
                    base = market['base']
                    usd_pairs.append(f"{base}USDT")

            # Sort by volume if available, otherwise return as-is
            # Limit to top 100
            return usd_pairs[:100]

        except Exception as e:
            logger.error(f"Error fetching top coins: {e}")
            # Fallback to common coins
            return [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT",
                "ADAUSDT", "AVAXUSDT", "SUIUSDT", "APTUSDT", "NEARUSDT", "OPUSDT",
                "ARBUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "ATOMUSDT", "FILUSDT"
            ]

    def scan_symbol(self, symbol: str) -> List[Pivot]:
        """Scan a symbol across all timeframes"""
        all_pivots = []

        for timeframe in TIMEFRAMES:
            # Add small delay between timeframes
            time.sleep(0.2)  # 200ms delay

            df = self.fetch_klines(symbol, timeframe)
            if df is None:
                continue

            pivots = self.detect_pivots(df, symbol, timeframe)
            all_pivots.extend(pivots)

            # Store detected pivots
            key = f"{symbol}_{timeframe}"
            self.detected_pivots[key] = pivots

        return all_pivots

    def update_watchlist(self):
        """Update watchlist with best setups"""
        watchlist_candidates = []

        # Get all symbols to scan
        symbols_to_scan = set(PRIORITY_COINS)

        # Add top 100 coins
        top_coins = self.get_top_100_coins()
        symbols_to_scan.update(top_coins[:50])  # Scan top 50 for efficiency

        logger.info(f"Scanning {len(symbols_to_scan)} symbols...")

        for symbol in symbols_to_scan:
            try:
                # Add delay between symbols to avoid rate limiting
                time.sleep(0.5)  # 500ms delay between symbols

                # Scan all timeframes
                pivots = self.scan_symbol(symbol)

                if not pivots:
                    continue

                # Get current price
                df_latest = self.fetch_klines(symbol, "5m", limit=10)
                if df_latest is None or len(df_latest) == 0:
                    continue

                current_price = df_latest.iloc[-1]['close']

                # Evaluate each pivot
                for pivot in pivots:
                    # Check for pullback
                    df = self.fetch_klines(symbol, pivot.timeframe, limit=100)
                    has_pullback, distance = self.check_pullback(df, pivot)

                    if has_pullback or pivot.confirmed:
                        # Calculate score
                        score = 0.0

                        # Quality bonus
                        if pivot.setup_quality == "TREND CHANGE":
                            score += 200  # Highest priority for trend change timeframes
                        elif pivot.setup_quality == "A+":
                            score += 100
                        elif pivot.setup_quality == "A":
                            score += 50
                        else:
                            score += 25

                        # Confirmed bonus
                        if pivot.confirmed:
                            score += 30

                        # Pullback bonus
                        if has_pullback:
                            score += 40
                            score -= distance * 2  # Closer = better

                        # Priority coin bonus (BTC, SOL, SUI)
                        if symbol in PRIORITY_COINS:
                            score += 20

                        # Probability-based scoring adjustments
                        # Higher timeframe = higher probability
                        if pivot.timeframe in TREND_CHANGE_TIMEFRAMES:
                            score += 100  # Trend change timeframes are highest priority
                        elif pivot.timeframe == "1h":
                            score += 30  # 1H pivots are most reliable
                        elif pivot.timeframe == "15m":
                            score += 15  # 15m pivots are good

                        # Pullback setups have higher probability than upcoming
                        if has_pullback:
                            score += 25  # Price already at zone = higher probability

                        # Confirmed pivots have higher probability
                        if pivot.confirmed:
                            score += 20  # Already confirmed = higher probability

                        setup_type = "PULLBACK" if has_pullback else "UPCOMING"

                        entry = WatchlistEntry(
                            symbol=symbol,
                            pivot=pivot,
                            current_price=current_price,
                            distance_to_pivot=distance,
                            setup_type=setup_type,
                            score=score
                        )

                        watchlist_candidates.append(entry)

            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue

        # Sort by score and take top entries
        watchlist_candidates.sort(key=lambda x: x.score, reverse=True)

        # Group by symbol and keep only the highest scoring entry per symbol
        symbol_best: Dict[str, WatchlistEntry] = {}
        for entry in watchlist_candidates:
            if entry.symbol not in symbol_best or entry.score > symbol_best[entry.symbol].score:
                symbol_best[entry.symbol] = entry

        # Convert back to list and sort by score (probability-based)
        unique_entries = list(symbol_best.values())
        unique_entries.sort(key=lambda x: x.score, reverse=True)

        # Prioritize BTC, SOL, SUI in watchlist, then best others
        priority_entries = [e for e in unique_entries if e.symbol in PRIORITY_COINS]
        other_entries = [e for e in unique_entries if e.symbol not in PRIORITY_COINS]

        # Combine: priority coins first, then best others
        # Ensure we have at least one priority coin if available
        if priority_entries:
            # Take all priority coins (up to MAX_WATCHLIST_SIZE)
            self.watchlist = priority_entries[:MAX_WATCHLIST_SIZE]
            # Add best others if we have room
            remaining_slots = MAX_WATCHLIST_SIZE - len(self.watchlist)
            if remaining_slots > 0:
                self.watchlist.extend(other_entries[:remaining_slots])
        else:
            # No priority coins found, use best others
            self.watchlist = other_entries[:MAX_WATCHLIST_SIZE]

        logger.info(f"Watchlist updated with {len(self.watchlist)} entries")

    def create_tradingview_link(self, symbol: str, timeframe: str) -> str:
        """Create TradingView chart link"""
        # Use COINBASE or KRAKEN exchange in TradingView
        exchange_name = "COINBASE" if USE_EXCHANGE == "coinbase" else "KRAKEN"
        base_symbol = symbol.replace("USDT", "")
        return f"https://www.tradingview.com/chart/?symbol={exchange_name}:{base_symbol}USD&interval={timeframe}"

    def send_discord_card(self, entry: WatchlistEntry):
        """Send Discord card for watchlist entry"""
        pivot = entry.pivot

        # Check if this is a trend change timeframe (super alert)
        is_trend_change = pivot.timeframe in TREND_CHANGE_TIMEFRAMES

        # Determine direction and color
        if pivot.pivot_type == "HIGH":
            direction = "SHORT"
            # Red for all alerts, darker red for trend change
            color = 0xCC0000 if is_trend_change else 0xFF0000  # Darker red for trend change
            emoji = "🔴"
            stop_placement = f"Stop above: ${pivot.price * 1.01:.4f}"
        else:
            direction = "LONG"
            # Red for trend change alerts, green for regular
            color = 0xCC0000 if is_trend_change else 0x00FF00  # Red for trend change
            emoji = "🔴" if is_trend_change else "🟢"
            stop_placement = f"Stop below: ${pivot.price * 0.99:.4f}"

        # Calculate entry and targets
        current_price = entry.current_price
        if pivot.pivot_type == "HIGH":
            entry_price = current_price
            target1 = pivot.price * 0.98  # 2% below pivot
            target2 = pivot.price * 0.95  # 5% below pivot
        else:
            entry_price = current_price
            target1 = pivot.price * 1.02  # 2% above pivot
            target2 = pivot.price * 1.05  # 5% above pivot

        tv_link = self.create_tradingview_link(entry.symbol, pivot.timeframe)

        # Add trend change indicator to title
        title_prefix = "🚨 TREND CHANGE ALERT 🚨" if is_trend_change else f"{emoji} PivotX Setup"
        quality_label = f"**{pivot.setup_quality}**" if is_trend_change else f"{pivot.setup_quality} Quality"

        embed = {
            "title": f"{title_prefix} - {entry.symbol}",
            "description": (
                f"**{direction} Setup** - {quality_label}\n\n"
                f"**Pivot {pivot.pivot_type}:** ${pivot.price:.4f}\n"
                f"**Timeframe:** {pivot.timeframe}\n"
                f"**Current Price:** ${current_price:.4f}\n"
                f"**Distance to Pivot:** {entry.distance_to_pivot:.2f}%\n"
                f"**Setup Type:** {entry.setup_type}\n"
                f"**{stop_placement}**\n\n"
                f"**Entry Zone:** ${entry_price:.4f}\n"
                f"**Target 1:** ${target1:.4f}\n"
                f"**Target 2:** ${target2:.4f}\n\n"
                f"**Pivot Location:** Bar {pivot.bar_index} ({pivot.timestamp.strftime('%Y-%m-%d %H:%M')} UTC)\n"
                f"**ATR:** ${pivot.atr:.4f}\n"
                f"**Confirmed:** {'✅' if pivot.confirmed else '⏳'}\n\n"
                f"[📊 View Chart]({tv_link})"
            ),
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"PivotX Scanner • Score: {entry.score:.1f}"
            },
            "url": tv_link
        }

        try:
            # Add @everyone ping for trend change alerts
            content = "@everyone" if is_trend_change else None

            payload = {"embeds": [embed]}
            if content:
                payload["content"] = content

            response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
            response.raise_for_status()
            alert_type = "TREND CHANGE" if is_trend_change else "regular"
            logger.info(f"✅ Sent {alert_type} Discord card for {entry.symbol} {pivot.timeframe}")
        except Exception as e:
            logger.error(f"Error sending Discord card: {e}")


    def run(self):
        """Main loop"""
        logger.info("🚀 PivotX Scanner Bot started")

        while True:
            try:
                logger.info("Starting scan cycle...")

                # Update watchlist
                self.update_watchlist()

                # Send individual cards for new high-score entries
                # Only send alerts for BTC, SOL, and SUI
                # Group by symbol to avoid duplicate alerts for same coin
                symbol_entries: Dict[str, WatchlistEntry] = {}

                for entry in self.watchlist:
                    # Only send alerts for priority coins (BTC, SOL, SUI)
                    if entry.symbol not in ALERT_COINS:
                        continue

                    if entry.score > 80:  # Only send high-score setups
                        # Track by symbol only - only one alert per coin
                        if entry.symbol not in symbol_entries:
                            symbol_entries[entry.symbol] = entry
                        else:
                            # Keep the highest scoring entry for each symbol
                            if entry.score > symbol_entries[entry.symbol].score:
                                symbol_entries[entry.symbol] = entry

                # Send one alert per symbol (highest score only) - only for BTC/SOL/SUI
                for symbol, entry in symbol_entries.items():
                    # Create unique key by symbol only to prevent duplicate alerts
                    card_key = f"{symbol}_{entry.pivot.timeframe}"
                    if card_key not in self.sent_cards:
                        self.send_discord_card(entry)
                        self.sent_cards.add(card_key)
                        time.sleep(1)  # Rate limiting

                # Clean old entries (keep last 200 to cover multiple scan cycles)
                if len(self.sent_cards) > 200:
                    # Keep last 100 entries
                    self.sent_cards = set(list(self.sent_cards)[-100:])

                logger.info(f"Scan complete. Waiting {SCAN_INTERVAL_SEC} seconds...")
                time.sleep(SCAN_INTERVAL_SEC)

            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    scanner = PivotXScanner()
    scanner.run()




