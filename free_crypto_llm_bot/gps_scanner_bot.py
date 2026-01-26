#!/usr/bin/env python3
"""
GPS (Golden Pocket Syndicate) Scanner Bot - MEXC Perpetual Futures
Scans ALL MEXC perpetual futures for coins sitting at or near their previous week GPS levels
and sends alerts to Discord webhook every 15 minutes.
"""
import ccxt
import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class GPSLevels:
    """Golden Pocket levels for a coin"""
    prev_week_high: float
    prev_week_low: float
    gp_high: float  # 61.8% retracement
    gp_low: float   # 65% retracement
    gp_mid: float   # Middle of GP zone


@dataclass
class CoinSignal:
    """Signal data for a coin near GPS"""
    symbol: str
    name: str
    current_price: float
    gps_levels: GPSLevels
    distance_to_gp: float  # Percentage distance to GP
    strength_score: float  # 0-100 strength indicator
    volume_24h: float
    change_24h: float
    rsi: Optional[float] = None
    volume_ratio: Optional[float] = None


class MEXCClient:
    """Client for fetching MEXC perpetual futures data"""

    def __init__(self):
        try:
            # Load ALL markets (not just swap) to get complete list
            self.exchange = ccxt.mexc({
                "enableRateLimit": True
            })
            self.exchange.load_markets()
            logger.info("✅ MEXC exchange initialized")
        except Exception as e:
            logger.error(f"Error initializing MEXC: {e}")
            raise

    def get_all_perp_symbols(self, include_inactive: bool = False) -> List[str]:
        """
        Get ALL MEXC perpetual futures symbols

        Args:
            include_inactive: If True, include inactive markets (default: False)
        """
        try:
            symbols = []
            active_count = 0
            inactive_count = 0

            for symbol, market in self.exchange.markets.items():
                # Filter for perpetual swap/futures contracts
                # MEXC uses type='swap' for perpetual futures
                is_perp = market.get('type') == 'swap'

                # Only USDT pairs
                if (is_perp and
                    market.get('quote', '').upper() == 'USDT' and
                    'USDT' in symbol.upper()):

                    is_active = market.get('active', True)

                    if is_active:
                        symbols.append(symbol)
                        active_count += 1
                    elif include_inactive:
                        symbols.append(symbol)
                        inactive_count += 1

            if include_inactive and inactive_count > 0:
                logger.info(f"📊 Found {len(symbols)} MEXC perpetual futures pairs ({active_count} active, {inactive_count} inactive)")
            else:
                logger.info(f"📊 Found {len(symbols)} MEXC perpetual futures pairs (all active)")

            return sorted(symbols)
        except Exception as e:
            logger.error(f"Error fetching MEXC symbols: {e}")
            return []

    def get_weekly_ohlc(self, symbol: str, limit: int = 14) -> Optional[List]:
        """
        Get daily OHLCV data for weekly GPS calculation

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT:USDT')
            limit: Number of days (default 14 for 2 weeks)

        Returns:
            List of OHLCV candles [timestamp, open, high, low, close, volume]
        """
        try:
            # Fetch daily candles
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=limit)
            if not ohlcv or len(ohlcv) < 7:
                return None
            return ohlcv
        except Exception as e:
            logger.debug(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get current ticker data"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.debug(f"Error fetching ticker for {symbol}: {e}")
            return None

    def calculate_prev_week_gps(self, ohlc_data: List) -> Optional[GPSLevels]:
        """
        Calculate previous week GPS levels from daily OHLC data

        GPS calculation (matching TradingView indicator):
        - Previous Week High/Low: Aggregate daily candles into weekly
        - GP High = pwHigh - (pwHigh - pwLow) * 0.618 (61.8% retracement)
        - GP Low = pwHigh - (pwHigh - pwLow) * 0.65 (65% retracement)
        """
        if not ohlc_data or len(ohlc_data) < 7:
            return None

        try:
            # OHLCV format: [timestamp_ms, open, high, low, close, volume]
            # Sort by timestamp (oldest first)
            sorted_data = sorted(ohlc_data, key=lambda x: x[0])

            # Get current week start (Monday of current week)
            now = datetime.now()
            days_since_monday = now.weekday()  # 0 = Monday
            current_week_start = now - timedelta(days=days_since_monday)
            current_week_start = current_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            # Previous week: 7 days before current week start
            prev_week_start = current_week_start - timedelta(days=7)
            prev_week_end = current_week_start

            prev_week_high = 0
            prev_week_low = float('inf')
            prev_week_candles = []

            # Find candles in previous week
            for candle in sorted_data:
                timestamp = datetime.fromtimestamp(candle[0] / 1000)
                if prev_week_start <= timestamp < prev_week_end:
                    prev_week_candles.append(candle)
                    prev_week_high = max(prev_week_high, candle[2])  # high
                    prev_week_low = min(prev_week_low, candle[3])      # low

            # If no candles found in previous week, use the week before current (last 7-14 days)
            if not prev_week_candles:
                # Use candles from 7-14 days ago
                two_weeks_ago = current_week_start - timedelta(days=14)
                for candle in sorted_data:
                    timestamp = datetime.fromtimestamp(candle[0] / 1000)
                    if two_weeks_ago <= timestamp < prev_week_start:
                        prev_week_high = max(prev_week_high, candle[2])
                        prev_week_low = min(prev_week_low, candle[3])

            # Fallback: if still no data, use first 7 candles
            if prev_week_high == 0 or prev_week_low == float('inf'):
                week_candles = sorted_data[:7] if len(sorted_data) >= 7 else sorted_data
                prev_week_high = max(c[2] for c in week_candles)
                prev_week_low = min(c[3] for c in week_candles)

            if prev_week_high <= prev_week_low or prev_week_high == 0:
                return None

            # Calculate GPS levels (matching TradingView formula)
            # pwGpHigh = pwHigh - (pwHigh - pwLow) * 0.618
            # pwGpLow = pwHigh - (pwHigh - pwLow) * 0.65
            range_size = prev_week_high - prev_week_low
            gp_high = prev_week_high - (range_size * 0.618)
            gp_low = prev_week_high - (range_size * 0.65)
            gp_mid = (gp_high + gp_low) / 2

            return GPSLevels(
                prev_week_high=prev_week_high,
                prev_week_low=prev_week_low,
                gp_high=gp_high,
                gp_low=gp_low,
                gp_mid=gp_mid
            )
        except Exception as e:
            logger.error(f"Error calculating GPS levels: {e}")
            return None

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI from price data"""
        if len(prices) < period + 1:
            return None

        try:
            gains = []
            losses = []

            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))

            if len(gains) < period:
                return None

            # Calculate average gain and loss
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return round(rsi, 2)
        except Exception as e:
            logger.debug(f"Error calculating RSI: {e}")
            return None

    def calculate_strength_score(self, ticker: Dict, gps_levels: GPSLevels,
                                  current_price: float, ohlc_data: List) -> float:
        """
        Calculate strength score (0-100) for potential bounce

        Factors (matching GPS indicator logic):
        - Volume (higher is better, shows interest)
        - Price momentum (showing strength: slight positive or recovering)
        - RSI (oversold but showing recovery: 30-55 for bullish bounce)
        - Distance to GP (closer is better)
        - Price action (holding above GP low shows strength)
        """
        score = 0.0

        # Volume factor (0-25 points) - shows market interest
        volume_24h = ticker.get('quoteVolume', 0) or ticker.get('baseVolume', 0) * current_price
        if volume_24h > 5_000_000:  # $5M+ volume (very strong)
            score += 25
        elif volume_24h > 1_000_000:  # $1M+ volume (strong)
            score += 20
        elif volume_24h > 500_000:  # $500K+ volume (moderate)
            score += 15
        elif volume_24h > 100_000:  # $100K+ volume (decent)
            score += 10

        # Price momentum (0-25 points) - showing strength for bounce
        change_24h = ticker.get('percentage', 0) or 0
        # Best: slight negative to moderate positive (showing recovery)
        if 0 <= change_24h <= 8:  # Positive momentum, not overextended
            score += 25
        elif -3 <= change_24h < 0:  # Slight negative, potential reversal
            score += 20
        elif -8 <= change_24h < -3:  # More negative but could bounce
            score += 12
        elif change_24h > 8:  # Too extended, might pullback
            score += 8

        # RSI factor (0-25 points) - oversold but recovering
        rsi = None
        if ohlc_data and len(ohlc_data) >= 15:
            closes = [c[4] for c in ohlc_data[-15:]]  # Last 15 closes
            rsi = self.calculate_rsi(closes)
            if rsi:
                # Best: Oversold but recovering (30-50)
                if 35 <= rsi <= 50:  # Sweet spot for bounce
                    score += 25
                elif 30 <= rsi < 35:  # Oversold, good bounce setup
                    score += 20
                elif 25 <= rsi < 30:  # Very oversold
                    score += 15
                elif 50 < rsi <= 55:  # Still reasonable
                    score += 12
                elif 55 < rsi <= 60:  # Getting extended
                    score += 8

        # Distance to GP (0-20 points) - closer is better
        gp_range = gps_levels.gp_high - gps_levels.gp_low
        if gp_range > 0:
            # Check if price is within GP zone or very close
            if gps_levels.gp_low <= current_price <= gps_levels.gp_high:
                # Inside GP zone - maximum points
                score += 20
            else:
                # Calculate distance as percentage of GP range
                if current_price < gps_levels.gp_low:
                    distance = gps_levels.gp_low - current_price
                else:
                    distance = current_price - gps_levels.gp_high

                distance_pct = (distance / gp_range) * 100
                if distance_pct <= 1.0:  # Within 1% of GP zone
                    score += 18
                elif distance_pct <= 2.0:  # Within 2% of GP zone
                    score += 15
                elif distance_pct <= 3.0:  # Within 3% of GP zone
                    score += 10

        # Price action strength (0-5 points) - holding above GP low
        if current_price >= gps_levels.gp_low:
            score += 5

        return min(100, round(score, 1))


class DiscordWebhook:
    """Discord webhook client for sending alerts"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def send_alert(self, signals: List[CoinSignal]) -> bool:
        """Send GPS alert to Discord - Separate cards for breakout (green) and breakdown (purple)"""
        if not signals:
            return True

        try:
            # Separate signals into breakout (bullish) and breakdown (bearish)
            breakout_signals = []  # Price near GP low, potential breakout UP
            breakdown_signals = []  # Price near GP high, potential breakdown DOWN

            for signal in signals:
                # Calculate position in GP zone
                gp_range = signal.gps_levels.gp_high - signal.gps_levels.gp_low
                if gp_range <= 0:
                    continue

                position_in_gp = ((signal.current_price - signal.gps_levels.gp_low) / gp_range) * 100

                # Determine if breakout (near GP low, bullish) or breakdown (near GP high, bearish)
                # Breakout: Price near GP low (0-40% of zone) - potential to break UP
                # Breakdown: Price near GP high (60-100% of zone) - potential to break DOWN
                if position_in_gp <= 40:
                    # Near GP low - potential breakout UP
                    breakout_signals.append((signal, position_in_gp))
                elif position_in_gp >= 60:
                    # Near GP high - potential breakdown DOWN
                    breakdown_signals.append((signal, position_in_gp))
                else:
                    # In middle zone - could go either way, assign based on momentum
                    if signal.change_24h > 0:
                        breakout_signals.append((signal, position_in_gp))
                    else:
                        breakdown_signals.append((signal, position_in_gp))

            # Sort by strength score (highest first) and take top 5
            breakout_signals.sort(key=lambda x: x[0].strength_score, reverse=True)
            breakdown_signals.sort(key=lambda x: x[0].strength_score, reverse=True)

            top_breakout = [s[0] for s in breakout_signals[:5]]
            top_breakdown = [s[0] for s in breakdown_signals[:5]]

            embeds = []

            # GREEN CARD: Top 5 Breakout Plays (Bullish)
            if top_breakout:
                fields = []
                for i, signal in enumerate(top_breakout, 1):
                    gp_range = signal.gps_levels.gp_high - signal.gps_levels.gp_low
                    position_in_gp = ((signal.current_price - signal.gps_levels.gp_low) / gp_range) * 100 if gp_range > 0 else 50

                    # Format price
                    if signal.current_price >= 1:
                        price_str = f"${signal.current_price:,.2f}"
                    elif signal.current_price >= 0.01:
                        price_str = f"${signal.current_price:,.4f}"
                    else:
                        price_str = f"${signal.current_price:.6f}"

                    rsi_text = f" | RSI: {signal.rsi:.1f}" if signal.rsi else ""
                    signal_header = f"**{i}. {signal.name}** ({signal.symbol.split('/')[0]}) - Strength: **{signal.strength_score}/100**{rsi_text}"

                    signal_details = (
                        f"💰 Price: {price_str} | 📈 {signal.change_24h:+.2f}%\n"
                        f"🎯 GP Low: ${signal.gps_levels.gp_low:,.6f} | GP High: ${signal.gps_levels.gp_high:,.6f}\n"
                        f"📍 {position_in_gp:.1f}% in zone | 💵 Vol: ${signal.volume_24h:,.0f}"
                    )

                    fields.append({
                        "name": signal_header,
                        "value": signal_details,
                        "inline": False
                    })

                breakout_embed = {
                    "title": "🟢 Top 5 Breakout Plays - Previous Week GPS",
                    "description": "Best probability coins for **BREAKOUT** (bullish) from Previous Week Golden Pocket",
                    "color": 0x00FF00,  # Green
                    "fields": fields,
                    "footer": {
                        "text": f"Breakout potential: Price near GP low, ready to break UP | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                embeds.append(breakout_embed)

            # PURPLE CARD: Top 5 Breakdown Plays (Bearish)
            if top_breakdown:
                fields = []
                for i, signal in enumerate(top_breakdown, 1):
                    gp_range = signal.gps_levels.gp_high - signal.gps_levels.gp_low
                    position_in_gp = ((signal.current_price - signal.gps_levels.gp_low) / gp_range) * 100 if gp_range > 0 else 50

                    # Format price
                    if signal.current_price >= 1:
                        price_str = f"${signal.current_price:,.2f}"
                    elif signal.current_price >= 0.01:
                        price_str = f"${signal.current_price:,.4f}"
                    else:
                        price_str = f"${signal.current_price:.6f}"

                    rsi_text = f" | RSI: {signal.rsi:.1f}" if signal.rsi else ""
                    signal_header = f"**{i}. {signal.name}** ({signal.symbol.split('/')[0]}) - Strength: **{signal.strength_score}/100**{rsi_text}"

                    signal_details = (
                        f"💰 Price: {price_str} | 📉 {signal.change_24h:+.2f}%\n"
                        f"🎯 GP Low: ${signal.gps_levels.gp_low:,.6f} | GP High: ${signal.gps_levels.gp_high:,.6f}\n"
                        f"📍 {position_in_gp:.1f}% in zone | 💵 Vol: ${signal.volume_24h:,.0f}"
                    )

                    fields.append({
                        "name": signal_header,
                        "value": signal_details,
                        "inline": False
                    })

                breakdown_embed = {
                    "title": "🟣 Top 5 Breakdown Plays - Previous Week GPS",
                    "description": "Best probability coins for **BREAKDOWN** (bearish) from Previous Week Golden Pocket",
                    "color": 0x9932CC,  # Purple/DarkViolet
                    "fields": fields,
                    "footer": {
                        "text": f"Breakdown potential: Price near GP high, ready to break DOWN | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                embeds.append(breakdown_embed)

            if not embeds:
                logger.info("No breakout or breakdown signals to send")
                return True

            # Send both cards
            content_text = f"🚀 **GPS Scanner Alert** - "
            if top_breakout:
                content_text += f"🟢 {len(top_breakout)} Breakout Play(s) | "
            if top_breakdown:
                content_text += f"🟣 {len(top_breakdown)} Breakdown Play(s)"

            payload = {
                "embeds": embeds,
                "content": content_text
            }

            response = self.session.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            if response.status_code == 204:
                logger.info(f"✅ Successfully sent {len(embeds)} GPS alert card(s) to Discord (Status: {response.status_code})")
                if top_breakout:
                    logger.info(f"   🟢 {len(top_breakout)} breakout plays (green)")
                if top_breakdown:
                    logger.info(f"   🟣 {len(top_breakdown)} breakdown plays (purple)")
            else:
                logger.warning(f"⚠️  Discord response: {response.status_code} - {response.text[:200]}")

            return True

        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            import traceback
            traceback.print_exc()
            return False


class GPSScannerBot:
    """Main GPS Scanner Bot for MEXC Perpetual Futures"""

    def __init__(self, webhook_url: str):
        self.webhook = DiscordWebhook(webhook_url)
        self.client = MEXCClient()
        self.scan_interval = 15 * 60  # 15 minutes in seconds
        self.symbols = []  # Will be populated on first scan

    def is_near_gps(self, price: float, gps_levels: GPSLevels, threshold: float = 3.0) -> bool:
        """
        Check if price is near GPS levels

        Args:
            price: Current price
            gps_levels: GPS levels
            threshold: Percentage threshold (default 3% to catch coins approaching GP)
        """
        gp_range = gps_levels.gp_high - gps_levels.gp_low
        if gp_range <= 0:
            return False

        # Check if price is within GP zone
        if gps_levels.gp_low <= price <= gps_levels.gp_high:
            return True

        # Check if price is within threshold% of GP zone boundaries
        if price < gps_levels.gp_low:
            distance = gps_levels.gp_low - price
            distance_pct = (distance / gps_levels.gp_low) * 100
        else:
            distance = price - gps_levels.gp_high
            distance_pct = (distance / gps_levels.gp_high) * 100

        return distance_pct <= threshold

    def scan_coin(self, symbol: str) -> Optional[CoinSignal]:
        """Scan a single coin for GPS signals"""
        try:
            # Get current ticker data
            ticker = self.client.get_ticker(symbol)
            if not ticker:
                return None

            current_price = ticker.get('last', 0) or ticker.get('close', 0)
            if current_price <= 0:
                return None

            # Get weekly OHLC data
            ohlc_data = self.client.get_weekly_ohlc(symbol, limit=14)
            if not ohlc_data:
                return None

            # Calculate previous week GPS
            gps_levels = self.client.calculate_prev_week_gps(ohlc_data)
            if not gps_levels:
                return None

            # Check if near GPS
            if not self.is_near_gps(current_price, gps_levels, threshold=3.0):
                return None

            # Calculate strength score
            strength_score = self.client.calculate_strength_score(
                ticker, gps_levels, current_price, ohlc_data
            )

            # Only return signals with meaningful strength (>= 40 for better quality)
            if strength_score < 40:
                return None

            # Calculate distance to GP
            distance_to_gp = abs(current_price - gps_levels.gp_mid) / gps_levels.gp_mid * 100

            # Calculate RSI if possible
            rsi = None
            if len(ohlc_data) >= 15:
                closes = [c[4] for c in ohlc_data[-15:]]
                rsi = self.client.calculate_rsi(closes)

            # Get coin name
            coin_name = symbol.split('/')[0] if '/' in symbol else symbol.split(':')[0]

            # Get volume
            volume_24h = ticker.get('quoteVolume', 0) or (ticker.get('baseVolume', 0) * current_price)
            change_24h = ticker.get('percentage', 0) or 0

            return CoinSignal(
                symbol=symbol,
                name=coin_name,
                current_price=current_price,
                gps_levels=gps_levels,
                distance_to_gp=distance_to_gp,
                strength_score=strength_score,
                volume_24h=volume_24h,
                change_24h=change_24h,
                rsi=rsi
            )

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")
            return None

    def scan_all_coins(self) -> List[CoinSignal]:
        """Scan all MEXC perpetual futures and return signals"""
        signals = []

        # Get all symbols if not already loaded
        if not self.symbols:
            logger.info("Loading MEXC perpetual futures symbols...")
            self.symbols = self.client.get_all_perp_symbols()
            if not self.symbols:
                logger.error("No symbols found! Check MEXC connection.")
                return []

        logger.info(f"Scanning {len(self.symbols)} MEXC perpetual futures for GPS signals...")

        scanned = 0
        errors = 0
        for symbol in self.symbols:
            try:
                signal = self.scan_coin(symbol)
                if signal:
                    signals.append(signal)
                    logger.info(f"✅ Found GPS signal: {signal.name} ({signal.symbol}) - Strength: {signal.strength_score}/100")
            except Exception as e:
                errors += 1
                if errors <= 5:  # Log first 5 errors
                    logger.debug(f"Error scanning {symbol}: {e}")

            scanned += 1
            if scanned % 50 == 0:
                logger.info(f"Progress: {scanned}/{len(self.symbols)} symbols scanned... (errors: {errors})")

            # Rate limiting - be nice to the API
            time.sleep(0.1)  # 100ms delay between requests

        if errors > 0:
            logger.warning(f"⚠️  Encountered {errors} errors during scan (some symbols may have been skipped)")

        # Sort by strength score (highest first)
        signals.sort(key=lambda x: x.strength_score, reverse=True)

        # Return all signals - webhook will filter to top 5 breakout + top 5 breakdown
        logger.info(f"Scan complete: Found {len(signals)} GPS signals out of {len(self.symbols)} symbols")
        logger.info(f"📊 Will send top 5 breakout plays (green) + top 5 breakdown plays (purple)")

        return signals

    def run_scan_loop(self):
        """Run continuous scan loop every 15 minutes"""
        logger.info("=" * 60)
        logger.info("🚀 Starting GPS Scanner Bot - MEXC Perpetual Futures")
        logger.info("=" * 60)
        logger.info(f"Scan interval: {self.scan_interval / 60} minutes")
        logger.info("")

        # Run first scan immediately
        try:
            logger.info(f"⏰ Starting initial scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("-" * 60)

            signals = self.scan_all_coins()

            if signals:
                logger.info(f"📢 Found {len(signals)} GPS signals, sending to Discord...")
                success = self.webhook.send_alert(signals)
                if success:
                    logger.info("✅ Alerts sent successfully to Discord!")
                else:
                    logger.error("❌ Failed to send alerts to Discord")
            else:
                logger.info("ℹ️  No GPS signals found in this scan")

            logger.info("-" * 60)
        except Exception as e:
            logger.error(f"❌ Error in initial scan: {e}")
            import traceback
            traceback.print_exc()

        while True:
            try:
                logger.info(f"⏰ Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("-" * 60)

                signals = self.scan_all_coins()

                if signals:
                    logger.info(f"📢 Found {len(signals)} GPS signals, sending to Discord...")
                    success = self.webhook.send_alert(signals)
                    if success:
                        logger.info("✅ Alerts sent successfully to Discord!")
                    else:
                        logger.error("❌ Failed to send alerts to Discord")
                else:
                    logger.info("ℹ️  No GPS signals found in this scan")

                logger.info("-" * 60)
                logger.info(f"⏳ Next scan in {self.scan_interval / 60} minutes...")
                logger.info("")
                time.sleep(self.scan_interval)

            except KeyboardInterrupt:
                logger.info("")
                logger.info("🛑 Scanner stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in scan loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """Main entry point"""
    # Discord webhook URL
    WEBHOOK_URL = ""

    bot = GPSScannerBot(WEBHOOK_URL)
    bot.run_scan_loop()


if __name__ == "__main__":
    main()
