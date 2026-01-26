"""
Pocket Option Market Scanner Bot

Scans underlying markets to generate accurate signals for binary options trading.
Uses real exchange data (since Pocket Option prices are derived from underlying markets)
and applies Bounty Seeker signal detection logic (ORB, FVG, SFP, Single Prints).
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import time
import logging
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pocket_option_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal data structure"""
    symbol: str
    direction: str  # 'CALL' or 'PUT' for binary options
    confidence: float  # 0-100
    grade: str  # A+, A, B, C
    entry_price: float
    timeframe: str
    signal_type: str  # ORB, FVG, SFP, SP, etc.
    confluence_score: int
    reasons: List[str]
    timestamp: datetime


class PocketOptionScanner:
    """
    Scanner that analyzes underlying markets to generate binary options signals.

    Pocket Option uses prices from real markets, so we scan those markets
    using your Bounty Seeker logic (ORB, FVG, SFP, Single Prints, Pivots).
    """

    def __init__(self, webhook_url: Optional[str] = None, telegram_bot_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None, symbols: Optional[List[str]] = None):
        """
        Initialize scanner

        Args:
            webhook_url: Discord webhook for notifications
            telegram_bot_token: Telegram bot token from @BotFather
            telegram_chat_id: Telegram chat ID (your user ID or group ID)
            symbols: List of symbols to scan (default: major pairs/assets)
        """
        # Default symbols commonly traded on Pocket Option
        self.symbols = symbols or [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'EUR/USD', 'GBP/USD',
            'USD/JPY', 'AUD/USD', 'XAU/USD', 'SPX500', 'NAS100'
        ]

        # Exchange for market data (Pocket Option likely uses aggregators)
        self.exchange_id = 'binance'  # Primary source
        self.exchange = None
        self.backup_exchanges = ['bybit', 'okx', 'kraken']

        # Signal detection parameters (from Pine script)
        self.pivot_lookback = 10
        self.min_volume_mult = 1.0
        self.strong_volume_mult = 1.5
        self.sfp_merge_distance = 0.5  # %
        self.min_touches_for_strong = 2

        # ORB settings
        self.orb_start_hour = 9
        self.orb_start_minute = 30
        self.orb_end_hour = 9
        self.orb_end_minute = 45
        self.orb_timezone = 'GMT-5'

        # Signal storage
        self.recent_signals: deque = deque(maxlen=100)
        self.sfp_history: Dict[str, List[Dict]] = {}  # Track SFPs per symbol
        self.orb_levels: Dict[str, Dict] = {}  # Track ORB levels

        # Notifications
        self.webhook_url = webhook_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

        # Initialize exchange
        self._init_exchange()

        logger.info(f"Scanner initialized - Tracking {len(self.symbols)} symbols")

    def _init_exchange(self):
        """Initialize exchange connection"""
        exchanges_to_try = [self.exchange_id] + self.backup_exchanges

        for ex_id in exchanges_to_try:
            try:
                exchange_class = getattr(ccxt, ex_id)
                self.exchange = exchange_class({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}  # Spot for binary options underlying
                })
                self.exchange.load_markets()
                logger.info(f"✅ Connected to {ex_id}")
                self.exchange_id = ex_id
                return
            except Exception as e:
                logger.warning(f"⚠️ {ex_id} failed: {e}")
                continue

        raise Exception("Could not connect to any exchange")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a symbol"""
        try:
            # Try to find the symbol on exchange
            exchange_symbol = self._find_symbol(symbol)
            if not exchange_symbol:
                return None

            ohlcv = self.exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return None

    def _find_symbol(self, symbol: str) -> Optional[str]:
        """Find symbol on exchange, handle different formats"""
        # Try exact match
        if symbol in self.exchange.markets:
            return symbol

        # Try common variants
        variants = [
            symbol,
            symbol.replace('USDT', 'USD'),
            symbol.replace('USD', 'USDT'),
        ]

        for variant in variants:
            if variant in self.exchange.markets:
                return variant

        return None

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        return true_range.rolling(period).mean()

    def detect_pivots(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        Detect pivot highs and lows (from Pine script logic)
        Returns: (pivot_highs, pivot_lows)
        """
        vol_sma = df['volume'].rolling(20).mean()
        atr = self.calculate_atr(df)
        price_range = df['high'].rolling(self.pivot_lookback).max() - df['low'].rolling(self.pivot_lookback).min()

        # Detect pivot highs
        pivot_highs = pd.Series(index=df.index, dtype=float)
        for i in range(self.pivot_lookback, len(df) - self.pivot_lookback):
            is_pivot = True
            for j in range(i - self.pivot_lookback, i + self.pivot_lookback + 1):
                if j != i and df['high'].iloc[j] >= df['high'].iloc[i]:
                    is_pivot = False
                    break
            if is_pivot and df['volume'].iloc[i] > vol_sma.iloc[i] * self.min_volume_mult:
                pivot_highs.iloc[i] = df['high'].iloc[i]

        # Detect pivot lows
        pivot_lows = pd.Series(index=df.index, dtype=float)
        for i in range(self.pivot_lookback, len(df) - self.pivot_lookback):
            is_pivot = True
            for j in range(i - self.pivot_lookback, i + self.pivot_lookback + 1):
                if j != i and df['low'].iloc[j] <= df['low'].iloc[i]:
                    is_pivot = False
                    break
            if is_pivot and df['volume'].iloc[i] > vol_sma.iloc[i] * self.min_volume_mult:
                pivot_lows.iloc[i] = df['low'].iloc[i]

        return pivot_highs, pivot_lows

    def detect_sfps(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Detect Support/Resistance Points (SFPs) with touch counting
        Returns dict with SFP levels and their strength
        """
        pivot_highs, pivot_lows = self.detect_pivots(df)
        vol_sma = df['volume'].rolling(20).mean()

        # Get recent pivots
        recent_highs = []
        recent_lows = []

        for i in range(len(df) - 50, len(df)):  # Last 50 bars
            if not pd.isna(pivot_highs.iloc[i]):
                recent_highs.append({
                    'price': pivot_highs.iloc[i],
                    'bar': i,
                    'volume': df['volume'].iloc[i]
                })
            if not pd.isna(pivot_lows.iloc[i]):
                recent_lows.append({
                    'price': pivot_lows.iloc[i],
                    'bar': i,
                    'volume': df['volume'].iloc[i]
                })

        # Merge similar levels and count touches
        resistance_levels = []
        support_levels = []

        # Process resistance (pivot highs)
        for pivot in recent_highs:
            merged = False
            for res in resistance_levels:
                price_diff_pct = abs(pivot['price'] - res['price']) / res['price'] * 100
                if price_diff_pct < self.sfp_merge_distance:
                    # Merge - count as touch
                    res['touches'] += 1
                    res['price'] = max(res['price'], pivot['price'])  # Use higher price
                    merged = True
                    break

            if not merged:
                resistance_levels.append({
                    'price': pivot['price'],
                    'touches': 1,
                    'bar': pivot['bar'],
                    'volume': pivot['volume']
                })

        # Process support (pivot lows)
        for pivot in recent_lows:
            merged = False
            for sup in support_levels:
                price_diff_pct = abs(pivot['price'] - sup['price']) / sup['price'] * 100
                if price_diff_pct < self.sfp_merge_distance:
                    sup['touches'] += 1
                    sup['price'] = min(sup['price'], pivot['price'])  # Use lower price
                    merged = True
                    break

            if not merged:
                support_levels.append({
                    'price': pivot['price'],
                    'touches': 1,
                    'bar': pivot['bar'],
                    'volume': pivot['volume']
                })

        # Calculate strength
        current_price = df['close'].iloc[-1]
        current_vol = df['volume'].iloc[-1]
        vol_avg = vol_sma.iloc[-1]

        # Find nearest levels
        nearest_resistance = None
        nearest_support = None

        for res in resistance_levels:
            if res['price'] > current_price:
                if nearest_resistance is None or res['price'] < nearest_resistance['price']:
                    # Calculate strength
                    is_strong_vol = res['volume'] > vol_avg * self.strong_volume_mult
                    strength = 0
                    if res['touches'] >= self.min_touches_for_strong:
                        strength += 2
                    elif res['touches'] >= 1:
                        strength += 1
                    if is_strong_vol:
                        strength += 1
                    res['strength'] = strength
                    nearest_resistance = res

        for sup in support_levels:
            if sup['price'] < current_price:
                if nearest_support is None or sup['price'] > nearest_support['price']:
                    is_strong_vol = sup['volume'] > vol_avg * self.strong_volume_mult
                    strength = 0
                    if sup['touches'] >= self.min_touches_for_strong:
                        strength += 2
                    elif sup['touches'] >= 1:
                        strength += 1
                    if is_strong_vol:
                        strength += 1
                    sup['strength'] = strength
                    nearest_support = sup

        return {
            'resistance': nearest_resistance,
            'support': nearest_support,
            'all_resistance': resistance_levels,
            'all_support': support_levels,
            'current_price': current_price
        }

    def detect_fvg(self, df: pd.DataFrame) -> List[Dict]:
        """Detect Fair Value Gaps"""
        vol_sma = df['volume'].rolling(20).mean()
        fvgs = []

        for i in range(2, len(df)):
            # Bullish FVG: gap up
            if df['high'].iloc[i-1] < df['low'].iloc[i] and df['volume'].iloc[i] > vol_sma.iloc[i] * 0.8:
                fvgs.append({
                    'type': 'BULLISH',
                    'top': df['high'].iloc[i-1],
                    'bottom': df['low'].iloc[i],
                    'bar': i,
                    'volume': df['volume'].iloc[i]
                })

            # Bearish FVG: gap down
            if df['low'].iloc[i-1] > df['high'].iloc[i] and df['volume'].iloc[i] > vol_sma.iloc[i] * 0.8:
                fvgs.append({
                    'type': 'BEARISH',
                    'top': df['low'].iloc[i-1],
                    'bottom': df['high'].iloc[i],
                    'bar': i,
                    'volume': df['volume'].iloc[i]
                })

        # Return recent FVGs (last 20 bars)
        return [fvg for fvg in fvgs if fvg['bar'] >= len(df) - 20]

    def detect_single_prints(self, df: pd.DataFrame, lookback: int = 20) -> List[Dict]:
        """Detect Single Print levels (unique highs/lows)"""
        vol_sma = df['volume'].rolling(20).mean()
        single_prints = []

        for i in range(1, min(lookback, len(df))):
            h = df['high'].iloc[-i]
            l = df['low'].iloc[-i]

            # Check if high is unique
            h_count = sum(1 for j in range(len(df)) if abs(df['high'].iloc[j] - h) / h < 0.001)
            if h_count == 1 and df['volume'].iloc[-i] > vol_sma.iloc[-i] * 1.2:
                single_prints.append({
                    'price': h,
                    'type': 'HIGH',
                    'bar': len(df) - i
                })

            # Check if low is unique
            l_count = sum(1 for j in range(len(df)) if abs(df['low'].iloc[j] - l) / l < 0.001)
            if l_count == 1 and df['volume'].iloc[-i] > vol_sma.iloc[-i] * 1.2:
                single_prints.append({
                    'price': l,
                    'type': 'LOW',
                    'bar': len(df) - i
                })

        return single_prints

    def calculate_orb(self, df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """
        Calculate Opening Range Breakout (ORB) levels
        Uses first 15 minutes of trading session
        """
        # Reset ORB daily
        today = datetime.now().date()
        if symbol not in self.orb_levels or self.orb_levels[symbol].get('date') != today:
            # Find opening range (first 15 minutes = 3 bars on 5m chart)
            if len(df) < 3:
                return None

            orb_high = df['high'].iloc[:3].max()
            orb_low = df['low'].iloc[:3].min()

            self.orb_levels[symbol] = {
                'high': orb_high,
                'low': orb_low,
                'date': today
            }

        orb_data = self.orb_levels[symbol]
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]

        # Check for breakouts
        orb_break = None
        if current_high > orb_data['high']:
            orb_break = 'BREAKOUT_UP'
        elif current_low < orb_data['low']:
            orb_break = 'BREAKOUT_DOWN'

        return {
            'high': orb_data['high'],
            'low': orb_data['low'],
            'current_price': current_price,
            'break': orb_break
        }

    def generate_signal(self, symbol: str, df: pd.DataFrame, timeframe: str = '5m') -> Optional[Signal]:
        """
        Generate trading signal by combining all detection methods
        Returns Signal object if conditions are met
        """
        if df is None or len(df) < 100:
            return None

        # Run all detectors
        sfp_data = self.detect_sfps(df, symbol)
        fvgs = self.detect_fvg(df)
        single_prints = self.detect_single_prints(df)
        orb_data = self.calculate_orb(df, symbol)

        current_price = df['close'].iloc[-1]
        vol_avg = df['volume'].rolling(20).mean().iloc[-1]
        current_vol = df['volume'].iloc[-1]

        # Build confluence score
        confluence = 0
        reasons = []
        signal_type = []

        # SFP signals (40 points)
        if sfp_data['resistance'] and sfp_data['resistance']['strength'] >= 2:
            price_dist = abs(current_price - sfp_data['resistance']['price']) / sfp_data['resistance']['price'] * 100
            if price_dist < 0.5:  # Within 0.5% of resistance
                confluence += 25
                reasons.append(f"Strong Resistance SFP ({sfp_data['resistance']['touches']} touches)")
                signal_type.append('SFP_RESISTANCE')

        if sfp_data['support'] and sfp_data['support']['strength'] >= 2:
            price_dist = abs(current_price - sfp_data['support']['price']) / sfp_data['support']['price'] * 100
            if price_dist < 0.5:  # Within 0.5% of support
                confluence += 25
                reasons.append(f"Strong Support SFP ({sfp_data['support']['touches']} touches)")
                signal_type.append('SFP_SUPPORT')

        # ORB signals (30 points)
        if orb_data and orb_data['break']:
            if orb_data['break'] == 'BREAKOUT_UP':
                confluence += 30
                reasons.append("ORB High Breakout")
                signal_type.append('ORB_BULLISH')
            elif orb_data['break'] == 'BREAKOUT_DOWN':
                confluence += 30
                reasons.append("ORB Low Breakdown")
                signal_type.append('ORB_BEARISH')

        # FVG signals (20 points)
        recent_fvg = [fvg for fvg in fvgs if fvg['bar'] == len(df) - 1]
        if recent_fvg:
            fvg = recent_fvg[0]
            if fvg['type'] == 'BULLISH':
                confluence += 20
                reasons.append("Bullish FVG Formed")
                signal_type.append('FVG_BULLISH')
            elif fvg['type'] == 'BEARISH':
                confluence += 20
                reasons.append("Bearish FVG Formed")
                signal_type.append('FVG_BEARISH')

        # Volume confirmation (10 points)
        if current_vol > vol_avg * 1.5:
            confluence += 10
            reasons.append(f"High Volume ({current_vol/vol_avg:.1f}x avg)")
            signal_type.append('VOLUME')

        # Single Print confirmation (15 points)
        if single_prints:
            for sp in single_prints:
                price_dist = abs(current_price - sp['price']) / sp['price'] * 100
                if price_dist < 0.3:
                    confluence += 15
                    reasons.append(f"Single Print {sp['type']} Level")
                    signal_type.append('SP')
                    break

        # Need minimum confluence of 50 for signal
        if confluence < 50:
            return None

        # Determine direction
        long_signals = sum(1 for st in signal_type if 'BULLISH' in st or 'UP' in st or 'SUPPORT' in st)
        short_signals = sum(1 for st in signal_type if 'BEARISH' in st or 'DOWN' in st or 'RESISTANCE' in st)

        if long_signals > short_signals:
            direction = 'CALL'  # Binary options: CALL = up
        elif short_signals > long_signals:
            direction = 'PUT'  # Binary options: PUT = down
        else:
            return None  # No clear direction

        # Calculate confidence and grade
        confidence = min(confluence, 95)  # Cap at 95%

        if confluence >= 85:
            grade = 'A+'
        elif confluence >= 70:
            grade = 'A'
        elif confluence >= 60:
            grade = 'B'
        else:
            grade = 'C'

        signal = Signal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            grade=grade,
            entry_price=current_price,
            timeframe=timeframe,
            signal_type=', '.join(signal_type),
            confluence_score=confluence,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc)
        )

        return signal

    def scan_symbol(self, symbol: str, timeframes: List[str] = ['5m', '15m']) -> List[Signal]:
        """Scan a symbol across multiple timeframes"""
        signals = []

        for tf in timeframes:
            try:
                df = self.fetch_ohlcv(symbol, timeframe=tf, limit=500)
                if df is None:
                    continue

                signal = self.generate_signal(symbol, df, tf)
                if signal:
                    signals.append(signal)

            except Exception as e:
                logger.error(f"Error scanning {symbol} on {tf}: {e}")
                continue

        return signals

    def scan_all_markets(self, timeframes: List[str] = ['5m', '15m']) -> List[Signal]:
        """Scan all configured markets"""
        logger.info(f"🔍 Scanning {len(self.symbols)} symbols...")

        all_signals = []
        for symbol in self.symbols:
            try:
                signals = self.scan_symbol(symbol, timeframes)
                all_signals.extend(signals)

                if signals:
                    logger.info(f"✅ {symbol}: {len(signals)} signal(s) found")
                    for sig in signals:
                        logger.info(f"   {sig.direction} {sig.grade} - {sig.confidence:.0f}% - {sig.signal_type}")

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue

        # Sort by confidence
        all_signals.sort(key=lambda x: x.confidence, reverse=True)

        return all_signals

    def send_discord_notification(self, signal: Signal):
        """Send signal notification to Discord"""
        if not self.webhook_url:
            return

        direction_emoji = "🟢" if signal.direction == 'CALL' else "🔴"
        color = 0x00ff00 if signal.direction == 'CALL' else 0xff0000

        embed = {
            "title": f"{direction_emoji} Pocket Option Signal: {signal.symbol} {signal.direction}",
            "description": f"**Grade:** {signal.grade} | **Confidence:** {signal.confidence:.0f}%",
            "color": color,
            "timestamp": signal.timestamp.isoformat(),
            "fields": [
                {"name": "Entry Price", "value": f"${signal.entry_price:.5f}", "inline": True},
                {"name": "Timeframe", "value": signal.timeframe, "inline": True},
                {"name": "Confluence", "value": f"{signal.confluence_score}/100", "inline": True},
                {"name": "Signal Type", "value": signal.signal_type, "inline": False},
                {"name": "Reasons", "value": "\n".join(signal.reasons), "inline": False},
            ],
            "footer": {"text": f"Pocket Option Scanner • {self.exchange_id.upper()}"}
        }

        try:
            payload = {"embeds": [embed]}
            r = requests.post(self.webhook_url, json=payload, timeout=10)
            if r.status_code in (200, 201, 204):
                logger.info(f"✅ Discord notification sent for {signal.symbol}")
            else:
                logger.error(f"Discord error: {r.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    def send_telegram_notification(self, signal: Signal):
        """Send signal notification to Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return

        direction_emoji = "🟢" if signal.direction == 'CALL' else "🔴"
        direction_text = "📈 CALL (UP)" if signal.direction == 'CALL' else "📉 PUT (DOWN)"

        # Format message with emojis and structure
        message = f"""
{direction_emoji} <b>Pocket Option Signal</b>

<b>Symbol:</b> {signal.symbol}
<b>Direction:</b> {direction_text}
<b>Grade:</b> {signal.grade} | <b>Confidence:</b> {signal.confidence:.0f}%

<b>Entry Price:</b> ${signal.entry_price:,.5f}
<b>Timeframe:</b> {signal.timeframe}
<b>Confluence:</b> {signal.confluence_score}/100

<b>Signal Types:</b>
{signal.signal_type}

<b>Reasons:</b>
{chr(10).join('• ' + reason for reason in signal.reasons)}

<i>Timestamp: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
"""

        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }

            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                result = r.json()
                if result.get('ok'):
                    logger.info(f"✅ Telegram notification sent for {signal.symbol}")
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
            else:
                logger.error(f"Telegram HTTP error: {r.status_code} - {r.text}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def send_notifications(self, signal: Signal):
        """Send notifications to all configured channels"""
        self.send_discord_notification(signal)
        self.send_telegram_notification(signal)

    def run_continuous_scan(self, interval_seconds: int = 60, timeframes: List[str] = ['5m']):
        """Run continuous scanning loop"""
        logger.info("🚀 Pocket Option Scanner starting...")
        logger.info(f"📊 Symbols: {', '.join(self.symbols)}")
        logger.info(f"⏰ Timeframes: {', '.join(timeframes)}")
        logger.info(f"🔄 Scan interval: {interval_seconds}s")
        logger.info("=" * 70)

        while True:
            try:
                signals = self.scan_all_markets(timeframes)

                if signals:
                    logger.info(f"\n✅ Found {len(signals)} signal(s):")
                    for sig in signals:
                        logger.info(f"   {sig.symbol} {sig.direction} ({sig.grade}) - {sig.confidence:.0f}% confidence")

                        # Send notification for high-grade signals
                        if sig.grade in ['A+', 'A']:
                            self.send_notifications(sig)
                            self.recent_signals.append(sig)
                else:
                    logger.info("⏳ No signals found this scan")

                logger.info(f"💤 Waiting {interval_seconds}s for next scan...\n")
                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                logger.info("\n⏹️ Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                time.sleep(interval_seconds)


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Pocket Option Market Scanner")
    parser.add_argument("--symbols", default=os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT,EUR/USD,GBP/USD"),
                       help="Comma-separated symbols to scan")
    parser.add_argument("--webhook", default=os.getenv("DISCORD_WEBHOOK", ""),
                       help="Discord webhook URL")
    parser.add_argument("--telegram-token", default=os.getenv("TELEGRAM_BOT_TOKEN", ""),
                       help="Telegram bot token from @BotFather")
    parser.add_argument("--telegram-chat-id", default=os.getenv("TELEGRAM_CHAT_ID", ""),
                       help="Telegram chat ID (user or group ID)")
    parser.add_argument("--interval", type=int, default=60,
                       help="Scan interval in seconds")
    parser.add_argument("--timeframes", default="5m,15m",
                       help="Comma-separated timeframes")
    parser.add_argument("--oneshot", action="store_true",
                       help="Run single scan then exit")

    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(',') if s.strip()]
    timeframes = [tf.strip() for tf in args.timeframes.split(',') if tf.strip()]

    scanner = PocketOptionScanner(
        webhook_url=args.webhook if args.webhook else None,
        telegram_bot_token=args.telegram_token if args.telegram_token else None,
        telegram_chat_id=args.telegram_chat_id if args.telegram_chat_id else None,
        symbols=symbols
    )

    if args.oneshot:
        signals = scanner.scan_all_markets(timeframes)
        if signals:
            print(f"\n✅ Found {len(signals)} signal(s):\n")
            for sig in signals:
                print(f"{sig.symbol} {sig.direction} ({sig.grade}) - {sig.confidence:.0f}%")
                print(f"  Type: {sig.signal_type}")
                print(f"  Reasons: {', '.join(sig.reasons)}\n")
        else:
            print("⏳ No signals found")
    else:
        scanner.run_continuous_scan(interval_seconds=args.interval, timeframes=timeframes)
