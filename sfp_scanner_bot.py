#!/usr/bin/env python3
"""
SFP Scanner Bot - Scans MEXC for Fair Value Gaps (SFPs) on 15m, 30m, and 1h
Finds coins approaching SFPs for potential reversal trades
"""

import time
import logging
import requests
import pandas as pd
import numpy as np
import ccxt
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ================== CONFIG ==================
DISCORD_WEBHOOK = ""
MIN_VOLUME_USD = 100_000  # Minimum 24h volume in USD
SCAN_INTERVAL = 1800  # 30 minutes in seconds
TIMEFRAMES = {
    '15m': '15m',
    '30m': '30m',
    '1h': '1h'
}
PICKS_PER_TIMEFRAME = 3  # 3 picks per timeframe = 9 total

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SFPLevel:
    """SFP (Fair Value Gap) level"""
    top: float
    bottom: float
    is_bullish: bool  # True for bullish gap, False for bearish gap
    bar_index: int
    timeframe: str


@dataclass
class SFPApproach:
    """Coin approaching an SFP"""
    symbol: str
    current_price: float
    sfp: SFPLevel
    distance_pct: float  # Distance to SFP in percentage
    direction: str  # 'LONG' if approaching bullish SFP from below, 'SHORT' if approaching bearish from above
    volume_24h: float


class SFPScanner:
    """SFP Scanner for Bybit perpetual futures"""

    def __init__(self, webhook_url: str, exchange_name: str = 'bybit'):
        self.webhook_url = webhook_url
        self.exchange = None
        self.pairs = []
        self.exchange_name = exchange_name.lower()

        # Stock tickers to exclude
        self.stock_tickers = {
            'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'NFLX', 'DIS',
            'V', 'JPM', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'PYPL', 'BAC', 'XOM', 'CVX',
            'ABBV', 'PFE', 'KO', 'AVGO', 'COST', 'PEP', 'TMO', 'ABT', 'MRK', 'CSCO', 'ACN',
            'ADBE', 'NKE', 'TXN', 'CMCSA', 'DHR', 'VZ', 'LIN', 'PM', 'NEE', 'RTX', 'HON',
            'UPS', 'QCOM', 'AMGN', 'T', 'LOW', 'INTU', 'SPGI', 'AMAT', 'DE', 'BKNG', 'C',
            'SBUX', 'AXP', 'ADI', 'ISRG', 'GILD', 'ADP', 'SYK', 'CL', 'MDT', 'TJX', 'ZTS',
            'GE', 'MMC', 'CI', 'APH', 'MO', 'SHW', 'ITW', 'WM', 'ETN', 'ICE', 'KLAC', 'CDNS',
            'SNPS', 'FTNT', 'MCHP', 'NXPI', 'CTAS', 'FAST', 'IDXX', 'PAYX', 'ODFL', 'CTSH',
            'AON', 'ANSS', 'KEYS', 'WDAY', 'ON', 'CDW', 'EXPD', 'FDS', 'BR', 'NDAQ', 'POOL',
            'CPRT', 'MCO', 'TTD', 'ZM', 'DOCN', 'DOCU', 'ROKU', 'PTON', 'SPOT', 'SNAP', 'TWTR',
            'SQ', 'SHOP', 'CRWD', 'OKTA', 'NET', 'DDOG', 'ZS', 'MDB', 'ESTC', 'NOW', 'TEAM',
            'PLTR', 'SNOW', 'RBLX', 'HOOD', 'COIN', 'LCID', 'RIVN', 'F', 'GM', 'FORD',
            'AMD', 'INTC', 'MU', 'LRCX', 'AMAT', 'KLAC', 'MCHP', 'SWKS', 'QRVO', 'MPWR',
            'ON', 'WOLF', 'ALGM', 'DIOD', 'POWI', 'SITM', 'CRUS', 'OLED', 'SMCI', 'SOFI', 'UPST', 'IWM', 'QQQ', 'SPY'
        }

        # Stablecoins list
        self.stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'PAXG', 'FDUSD', 'US', 'STBL']

    def is_stock_ticker(self, symbol: str) -> bool:
        """Check if symbol is a stock ticker"""
        # Extract base symbol
        base = symbol.split('/')[0].split(':')[0].upper()

        if base in self.stock_tickers or 'STOCK' in base:
            return True

        # Check for stock prefixes
        for stock in self.stock_tickers:
            if base.startswith(stock) and (base == stock or base.startswith(stock + 'STOCK')):
                return True

        return False

    def is_stablecoin_pair(self, symbol: str) -> bool:
        """Check if symbol is a stablecoin-to-stablecoin pair"""
        symbol_upper = symbol.upper()

        # Direct check for USDC/USDT in any format
        if 'USDC/USDT' in symbol_upper or 'USDT/USDC' in symbol_upper:
            return True

        # Remove :USDT suffix for parsing
        clean_symbol = symbol_upper.replace(':USDT', '').strip()

        if '/' in clean_symbol:
            parts = clean_symbol.split('/')
            if len(parts) >= 2:
                base = parts[0].strip()
                quote = parts[1].strip()

                # If both base and quote are stablecoins, exclude it
                if base in self.stablecoins and quote in self.stablecoins:
                    return True

                # Exclude ANY stablecoin against USDT (USDC/USDT, DAI/USDT, etc.)
                if base in self.stablecoins and quote == 'USDT':
                    return True
                if quote in self.stablecoins and base == 'USDT':
                    return True

        return False

    def initialize_exchange(self):
        """Initialize exchange (Bybit, OKX, or Kraken)"""
        try:
            if self.exchange_name == 'bybit':
                self.exchange = ccxt.bybit({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'swap'},
                    'timeout': 10000
                })
            elif self.exchange_name == 'okx' or self.exchange_name == 'okex':
                self.exchange = ccxt.okx({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'swap'},
                    'timeout': 10000
                })
            elif self.exchange_name == 'kraken':
                self.exchange = ccxt.kraken({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'swap'},
                    'timeout': 10000
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.exchange_name}")

            self.exchange.load_markets()
            logger.info(f"✅ {self.exchange_name.upper()} exchange initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.exchange_name.upper()}: {e}")
            raise

    def load_pairs_with_volume(self):
        """Load exchange pairs with volume > 100k USD, excluding stocks and stablecoin pairs"""
        logger.info(f"📊 Loading {self.exchange_name.upper()} pairs with volume > ${MIN_VOLUME_USD:,}...")

        try:
            # Get all tickers for volume data
            tickers = self.exchange.fetch_tickers()

            # Filter for perpetual futures
            valid_pairs = []
            excluded_stocks = 0
            excluded_stablecoins = 0

            for symbol, market in self.exchange.markets.items():
                # Check if it's a swap/perp futures contract
                if not (market.get('type') == 'swap' and market.get('active', True)):
                    continue

                # Check quote currency (USDT or USD)
                quote = market.get('quote', '').upper()
                if quote not in ['USDT', 'USD']:
                    continue

                # Exclude stock tickers
                if self.is_stock_ticker(symbol):
                    excluded_stocks += 1
                    continue

                # Exclude stablecoin pairs
                if self.is_stablecoin_pair(symbol):
                    excluded_stablecoins += 1
                    continue

                ticker = tickers.get(symbol, {})
                # quoteVolume is in USDT/USD equivalent
                volume_24h = ticker.get('quoteVolume', 0) or ticker.get('baseVolume', 0) * ticker.get('last', 0) or 0

                if volume_24h >= MIN_VOLUME_USD:
                    valid_pairs.append((symbol, volume_24h))

            # Sort by volume (descending)
            valid_pairs.sort(key=lambda x: x[1], reverse=True)
            self.pairs = [pair[0] for pair in valid_pairs]

            logger.info(f"✅ Loaded {len(self.pairs)} {self.exchange_name.upper()} pairs with volume > ${MIN_VOLUME_USD:,}")
            logger.info(f"   Excluded: {excluded_stocks} stock pairs, {excluded_stablecoins} stablecoin pairs")
            if len(self.pairs) > 0:
                logger.info(f"   Top 5 by volume: {', '.join(self.pairs[:5])}")

        except Exception as e:
            logger.error(f"❌ Error loading pairs: {e}")
            raise

    def detect_sfps_2candle(self, df: pd.DataFrame) -> List[SFPLevel]:
        """
        Detect SFPs using 2-candle gap method (more common)
        Bullish FVG: previous high < current low (gap up) OR small overlap
        Bearish FVG: previous low > current high (gap down) OR small overlap
        """
        sfps = []

        if len(df) < 2:
            return sfps

        for i in range(1, len(df)):
            h0, l0 = df['high'].iloc[i], df['low'].iloc[i]
            h1, l1 = df['high'].iloc[i-1], df['low'].iloc[i-1]
            c0, c1 = df['close'].iloc[i], df['close'].iloc[i-1]

            # Calculate overlap percentage
            overlap = min(h0, h1) - max(l0, l1)
            candle_size_0 = h0 - l0
            candle_size_1 = h1 - l1
            avg_size = (candle_size_0 + candle_size_1) / 2

            # Bullish FVG: gap up OR small overlap (< 30% of average candle size)
            if h1 < l0 or (overlap > 0 and overlap < avg_size * 0.3 and c0 > c1):
                gap_top = max(l0, h1)
                gap_bottom = min(h1, l0) if h1 < l0 else (h1 + l0) / 2
                sfp = SFPLevel(
                    top=gap_top,
                    bottom=gap_bottom,
                    is_bullish=True,
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

            # Bearish FVG: gap down OR small overlap (< 30% of average candle size)
            if l1 > h0 or (overlap > 0 and overlap < avg_size * 0.3 and c0 < c1):
                gap_top = max(l1, h0) if l1 > h0 else (l1 + h0) / 2
                gap_bottom = min(h0, l1)
                sfp = SFPLevel(
                    top=gap_top,
                    bottom=gap_bottom,
                    is_bullish=False,
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

        return sfps

    def detect_sfps_3candle(self, df: pd.DataFrame) -> List[SFPLevel]:
        """
        Detect SFPs using 3-candle FVG method (less common but more reliable)
        Bullish FVG: gap between candle[2].low and candle[0].high
        Bearish FVG: gap between candle[2].high and candle[0].low
        """
        sfps = []

        if len(df) < 3:
            return sfps

        for i in range(2, len(df)):
            h0, l0 = df['high'].iloc[i], df['low'].iloc[i]
            h2, l2 = df['high'].iloc[i-2], df['low'].iloc[i-2]

            # Bullish FVG: candle[2].low > candle[0].high (gap up)
            if l2 > h0:
                sfp = SFPLevel(
                    top=l2,
                    bottom=h0,
                    is_bullish=True,
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

            # Bearish FVG: candle[2].high < candle[0].low (gap down)
            if h2 < l0:
                sfp = SFPLevel(
                    top=l0,
                    bottom=h2,
                    is_bullish=False,
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

        return sfps

    def is_sfp_filled(self, sfp: SFPLevel, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if SFP has been filled (price has moved through it)"""
        if current_idx >= len(df):
            return False

        # Check if price has moved through the gap
        for i in range(sfp.bar_index, min(current_idx + 1, len(df))):
            low = df['low'].iloc[i]
            high = df['high'].iloc[i]

            # Filled if price has touched both top and bottom
            if low <= sfp.top and high >= sfp.bottom:
                return True

        return False

    def detect_pivot_levels(self, df: pd.DataFrame) -> List[SFPLevel]:
        """Detect recent pivot highs and lows as potential SFP zones"""
        sfps = []
        if len(df) < 10:
            return sfps

        # Look for pivot highs (resistance) and pivot lows (support) in last 50 bars
        lookback = 5
        for i in range(lookback, len(df) - lookback):
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]

            # Pivot high: higher than surrounding bars
            is_pivot_high = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df['high'].iloc[j] >= high:
                    is_pivot_high = False
                    break

            if is_pivot_high and i >= len(df) - 50:
                # Create a small zone around pivot high
                sfp = SFPLevel(
                    top=high * 1.002,  # 0.2% above
                    bottom=high * 0.998,  # 0.2% below
                    is_bullish=False,  # Resistance = bearish SFP
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

            # Pivot low: lower than surrounding bars
            is_pivot_low = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and df['low'].iloc[j] <= low:
                    is_pivot_low = False
                    break

            if is_pivot_low and i >= len(df) - 50:
                # Create a small zone around pivot low
                sfp = SFPLevel(
                    top=low * 1.002,  # 0.2% above
                    bottom=low * 0.998,  # 0.2% below
                    is_bullish=True,  # Support = bullish SFP
                    bar_index=i,
                    timeframe=''
                )
                sfps.append(sfp)

        return sfps

    def get_active_sfps(self, df: pd.DataFrame, timeframe: str) -> List[SFPLevel]:
        """Get active (unfilled) SFPs from recent data"""
        # Use multiple detection methods for more opportunities
        all_sfps_2c = self.detect_sfps_2candle(df)
        all_sfps_3c = self.detect_sfps_3candle(df)
        all_sfps_pivot = self.detect_pivot_levels(df)
        all_sfps = all_sfps_2c + all_sfps_3c + all_sfps_pivot
        current_idx = len(df) - 1

        # Filter out filled SFPs and keep only recent ones (last 100 bars)
        active_sfps = []
        seen_levels = set()  # Avoid duplicates

        for sfp in all_sfps:
            # Only keep SFPs from recent bars
            if sfp.bar_index >= len(df) - 100:
                if not self.is_sfp_filled(sfp, df, current_idx):
                    # Check for duplicates (similar price levels)
                    level_key = (round(sfp.top, 4), round(sfp.bottom, 4))
                    if level_key not in seen_levels:
                        seen_levels.add(level_key)
                        sfp.timeframe = timeframe
                        active_sfps.append(sfp)

        return active_sfps

    def calculate_distance_to_sfp(self, current_price: float, sfp: SFPLevel) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate distance to SFP and determine direction
        Returns: (distance_pct, direction) or (None, None) if not approaching
        """
        if sfp.is_bullish:
            # Bullish SFP (gap up) - looking for LONG opportunities
            # Price should be below the gap and approaching it
            if current_price < sfp.bottom:
                # Price is below the gap - potential LONG reversal when price reaches SFP
                distance = abs(sfp.bottom - current_price) / current_price * 100
                return distance, 'LONG'
            elif sfp.bottom <= current_price <= sfp.top:
                # Price is inside the gap - already at SFP
                return 0, 'LONG'
            else:
                # Price is above the gap - already filled or passed
                return None, None
        else:
            # Bearish SFP (gap down) - looking for SHORT opportunities
            # Price should be above the gap and approaching it
            if current_price > sfp.top:
                # Price is above the gap - potential SHORT reversal when price reaches SFP
                distance = abs(current_price - sfp.top) / current_price * 100
                return distance, 'SHORT'
            elif sfp.bottom <= current_price <= sfp.top:
                # Price is inside the gap - already at SFP
                return 0, 'SHORT'
            else:
                # Price is below the gap - already filled or passed
                return None, None

    def find_approaching_sfps(self, symbol: str, timeframe: str) -> List[SFPApproach]:
        """Find SFPs that price is approaching for a given symbol and timeframe"""
        try:
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
            if not ohlcv or len(ohlcv) < 10:
                return []

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Get active SFPs
            active_sfps = self.get_active_sfps(df, timeframe)
            if not active_sfps:
                return []

            current_price = df['close'].iloc[-1]

            # Get 24h volume
            ticker = self.exchange.fetch_ticker(symbol)
            volume_24h = ticker.get('quoteVolume', 0) or 0

            # Find approaching SFPs - simplified logic to catch ALL opportunities
            approaches = []
            for sfp in active_sfps:
                # Calculate distance to SFP zone (middle point)
                sfp_mid = (sfp.top + sfp.bottom) / 2
                abs_distance = abs(current_price - sfp_mid) / current_price * 100

                # Determine direction and approach status
                if sfp.is_bullish:
                    # Bullish SFP - gap up
                    if current_price < sfp.bottom:
                        # Price below gap - LONG opportunity
                        distance = abs(sfp.bottom - current_price) / current_price * 100
                        direction = 'LONG'
                    elif current_price > sfp.top:
                        # Price above gap - already filled
                        continue
                    else:
                        # Price inside gap
                        distance = 0
                        direction = 'LONG'
                else:
                    # Bearish SFP - gap down
                    if current_price > sfp.top:
                        # Price above gap - SHORT opportunity
                        distance = abs(current_price - sfp.top) / current_price * 100
                        direction = 'SHORT'
                    elif current_price < sfp.bottom:
                        # Price below gap - already filled
                        continue
                    else:
                        # Price inside gap
                        distance = 0
                        direction = 'SHORT'

                # Include if within 25% distance (very wide to catch opportunities)
                if distance <= 25.0:
                    approach = SFPApproach(
                        symbol=symbol,
                        current_price=current_price,
                        sfp=sfp,
                        distance_pct=distance,
                        direction=direction,
                        volume_24h=volume_24h
                    )
                    approaches.append(approach)

            # If multiple approaches for same symbol, keep the closest one
            if len(approaches) > 1:
                approaches.sort(key=lambda x: x.distance_pct)
                # Keep only the closest SFP per symbol
                seen_symbols = set()
                unique_approaches = []
                for approach in approaches:
                    if approach.symbol not in seen_symbols:
                        unique_approaches.append(approach)
                        seen_symbols.add(approach.symbol)
                approaches = unique_approaches

            return approaches

        except Exception as e:
            logger.debug(f"Error scanning {symbol} on {timeframe}: {e}")
            return []

    def scan_timeframe(self, timeframe: str) -> List[SFPApproach]:
        """Scan all pairs for approaching SFPs on a specific timeframe"""
        logger.info(f"🔍 Scanning {timeframe} timeframe...")
        all_approaches = []
        total_sfps_found = 0

        for i, symbol in enumerate(self.pairs):
            try:
                approaches = self.find_approaching_sfps(symbol, timeframe)
                all_approaches.extend(approaches)

                # Count SFPs found (for debugging)
                if approaches:
                    total_sfps_found += len(approaches)

                if (i + 1) % 50 == 0:
                    logger.info(f"   Scanned {i + 1}/{len(self.pairs)} pairs...")

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.debug(f"Error scanning {symbol}: {e}")
                continue

        # Sort by distance (closest first)
        all_approaches.sort(key=lambda x: x.distance_pct)

        logger.info(f"✅ Found {len(all_approaches)} SFPs on {timeframe} (within 20% distance)")
        return all_approaches

    def calculate_importance(self, approach: SFPApproach) -> float:
        """Calculate importance/probability percentage (0-100%)"""
        importance = 0.0

        # Factor 1: Distance to SFP (35% weight) - More lenient
        if approach.distance_pct == 0:
            distance_importance = 35.0  # Inside SFP = max
        elif approach.distance_pct <= 0.5:
            distance_importance = 32.0  # Very close
        elif approach.distance_pct <= 1.0:
            distance_importance = 28.0  # Close
        elif approach.distance_pct <= 2.0:
            distance_importance = 24.0  # Approaching
        elif approach.distance_pct <= 5.0:
            distance_importance = 18.0  # Getting close
        elif approach.distance_pct <= 10.0:
            distance_importance = 12.0  # Within range
        else:
            distance_importance = 5.0  # Far away
        importance += distance_importance

        # Factor 2: Volume quality (30% weight) - More lenient
        if approach.volume_24h >= 10_000_000:
            volume_importance = 30.0  # Very high volume
        elif approach.volume_24h >= 5_000_000:
            volume_importance = 25.0  # High volume
        elif approach.volume_24h >= 1_000_000:
            volume_importance = 20.0  # Good volume
        elif approach.volume_24h >= 500_000:
            volume_importance = 15.0  # Decent volume
        elif approach.volume_24h >= 250_000:
            volume_importance = 10.0  # Minimum volume
        else:
            volume_importance = 5.0  # Low volume
        importance += volume_importance

        # Factor 3: SFP quality (20% weight)
        sfp_size = abs(approach.sfp.top - approach.sfp.bottom) / approach.current_price * 100
        is_pivot = sfp_size < 0.5  # Small range = pivot point

        if is_pivot:
            sfp_importance = 20.0  # Pivot points are strong
        elif sfp_size >= 1.0:
            sfp_importance = 18.0  # Large gap = good
        elif sfp_size >= 0.5:
            sfp_importance = 15.0  # Medium gap
        else:
            sfp_importance = 12.0  # Small gap
        importance += sfp_importance

        # Factor 4: Setup quality (15% weight) - More lenient
        # Check if price is in ideal position for reversal
        if approach.distance_pct <= 1.0 and approach.volume_24h >= 1_000_000:
            setup_importance = 15.0  # Perfect setup
        elif approach.distance_pct <= 2.0:
            setup_importance = 13.0  # Good setup
        elif approach.distance_pct <= 5.0:
            setup_importance = 10.0  # Decent setup
        elif approach.distance_pct <= 10.0:
            setup_importance = 8.0  # Acceptable setup
        else:
            setup_importance = 5.0  # Weak setup
        importance += setup_importance

        return min(importance, 100.0)  # Cap at 100%

    def score_trade(self, approach: SFPApproach) -> float:
        """Score a trade for ranking"""
        importance = self.calculate_importance(approach)
        # Use importance as base score, weighted by volume for tie-breaking
        volume_multiplier = np.log10(max(approach.volume_24h, 1000)) / 10
        return importance * (1 + volume_multiplier)

    def get_best_trades(self, approaches: List[SFPApproach], limit: int = 3, min_importance: float = 80.0) -> List[SFPApproach]:
        """Get best trades (mix of LONG and SHORT) with minimum importance threshold"""
        if not approaches:
            return []

        # Filter by importance first (80%+ only)
        high_importance = []
        for approach in approaches:
            importance = self.calculate_importance(approach)
            if importance >= min_importance:
                high_importance.append((importance, approach))

        if not high_importance:
            return []

        # Sort by score (which includes importance)
        scored = [(self.score_trade(approach), importance, approach) for importance, approach in high_importance]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Get best trades with mix of LONG and SHORT
        best_trades = []
        long_trades = []
        short_trades = []

        for score, importance, approach in scored:
            if approach.direction == 'LONG':
                long_trades.append((importance, approach))
            else:
                short_trades.append((importance, approach))

        # Sort each side by importance
        long_trades.sort(key=lambda x: x[0], reverse=True)
        short_trades.sort(key=lambda x: x[0], reverse=True)

        # Alternate between LONG and SHORT, prioritizing highest importance
        seen_symbols = set()
        max_per_side = (limit + 1) // 2  # At least one of each if limit is odd

        # Add best LONG trades
        for importance, trade in long_trades:
            if trade.symbol not in seen_symbols and len(best_trades) < limit:
                best_trades.append(trade)
                seen_symbols.add(trade.symbol)
                if len([t for t in best_trades if t.direction == 'LONG']) >= max_per_side:
                    break

        # Add best SHORT trades
        for importance, trade in short_trades:
            if trade.symbol not in seen_symbols and len(best_trades) < limit:
                best_trades.append(trade)
                seen_symbols.add(trade.symbol)
                if len([t for t in best_trades if t.direction == 'SHORT']) >= max_per_side:
                    break

        # Fill remaining slots with highest importance regardless of direction
        for score, importance, approach in scored:
            if approach.symbol not in seen_symbols and len(best_trades) < limit:
                best_trades.append(approach)
                seen_symbols.add(approach.symbol)

        return best_trades[:limit]

    def get_watchlist_coins(self, approaches: List[SFPApproach], limit: int = 2, min_importance: float = 70.0) -> List[SFPApproach]:
        """Get coins approaching SFPs for watchlist (not ready to trade yet, but high importance)"""
        if not approaches:
            return []

        # Filter for coins that are approaching but not quite there yet (1-5% away)
        # AND have at least 70% importance (lower threshold for watchlist)
        approaching = []
        for a in approaches:
            if 1.0 <= a.distance_pct <= 5.0:
                importance = self.calculate_importance(a)
                if importance >= min_importance:
                    approaching.append((importance, a))

        if not approaching:
            return []

        # Sort by importance
        approaching.sort(key=lambda x: x[0], reverse=True)

        # Get top approaching coins
        watchlist = []
        seen_symbols = set()
        for importance, approach in approaching:
            if approach.symbol not in seen_symbols:
                watchlist.append(approach)
                seen_symbols.add(approach.symbol)
                if len(watchlist) >= limit:
                    break

        return watchlist

    def create_tradingview_link(self, symbol: str, timeframe: str) -> str:
        """Create TradingView link for symbol"""
        from urllib.parse import quote

        # Clean symbol - extract base ticker
        symbol_upper = symbol.upper().strip()

        # Remove :USDT or :USD suffix if present
        if ":USDT" in symbol_upper:
            symbol_upper = symbol_upper.replace(":USDT", "")
        if ":USD" in symbol_upper:
            symbol_upper = symbol_upper.replace(":USD", "")

        # Extract base ticker
        if "/USDT" in symbol_upper:
            ticker = symbol_upper.split("/USDT")[0]
            quote_currency = "USDT"
        elif "/USD" in symbol_upper:
            ticker = symbol_upper.split("/USD")[0]
            quote_currency = "USD"
        elif symbol_upper.endswith("USDT") and len(symbol_upper) > 4:
            ticker = symbol_upper[:-4]
            quote_currency = "USDT"
        elif symbol_upper.endswith("USD") and len(symbol_upper) > 3:
            ticker = symbol_upper[:-3]
            quote_currency = "USD"
        else:
            ticker = symbol_upper
            quote_currency = "USDT" if self.exchange_name != "kraken" else "USD"

        # Format based on exchange
        if self.exchange_name == "okx" or self.exchange_name == "okex":
            # OKX perpetual futures format: OKX:BTCUSDT.P
            ticker_formatted = f"{ticker}{quote_currency}.P"
            symbol_string = f"OKX:{ticker_formatted}"
        elif self.exchange_name == "kraken":
            # Kraken format: KRAKEN:BTCUSD
            ticker_formatted = f"{ticker}{quote_currency}"
            symbol_string = f"KRAKEN:{ticker_formatted}"
        elif self.exchange_name == "bybit":
            # Bybit format: BYBIT:BTCUSDT
            ticker_formatted = f"{ticker}{quote_currency}"
            symbol_string = f"BYBIT:{ticker_formatted}"
        else:
            # Default to BINANCE (most reliable)
            ticker_formatted = f"{ticker}{quote_currency}"
            symbol_string = f"BINANCE:{ticker_formatted}"

        # URL encode the symbol
        encoded_symbol = quote(symbol_string, safe='')

        return f"https://www.tradingview.com/chart/?symbol={encoded_symbol}&interval={timeframe}"

    def format_combined_card(self, trades_by_tf: Dict[str, List[SFPApproach]], watchlist: List[SFPApproach]) -> Dict:
        """Format single Discord card with all timeframes, trades, and watchlist"""
        embeds = []

        # Main trades embed
        description_parts = []

        # Group trades by timeframe
        for tf_key, tf_name in [('15m', '15m'), ('30m', '30m'), ('1h', '1h')]:
            trades = trades_by_tf.get(tf_key, [])
            if trades:
                description_parts.append(f"**━━━ {tf_name.upper()} TIMEFRAME ━━━**\n")

                for i, trade in enumerate(trades, 1):
                    sfp = trade.sfp
                    direction_emoji = "🟢" if trade.direction == 'LONG' else "🔴"
                    importance = self.calculate_importance(trade)

                    # Format distance
                    if trade.distance_pct == 0:
                        distance_str = "Inside SFP"
                    else:
                        distance_str = f"{trade.distance_pct:.2f}% away"

                    # Calculate targets
                    if trade.direction == 'LONG':
                        entry = trade.current_price
                        target1 = sfp.bottom * 1.01
                        target2 = sfp.top * 0.99
                        stop = entry * 0.98
                    else:
                        entry = trade.current_price
                        target1 = sfp.top * 0.99
                        target2 = sfp.bottom * 1.01
                        stop = entry * 1.02

                    tv_link = self.create_tradingview_link(trade.symbol, tf_name)

                    description_parts.append(
                        f"**{i}. {trade.symbol}** {direction_emoji} {trade.direction} | **{importance:.0f}% Importance**\n"
                        f"   Entry: ${entry:.6f} | Stop: ${stop:.6f}\n"
                        f"   T1: ${target1:.6f} | T2: ${target2:.6f}\n"
                        f"   Distance: {distance_str} | [Chart]({tv_link})\n"
                    )

                description_parts.append("")  # Spacing

        # Watchlist section
        if watchlist:
            description_parts.append("**━━━ 📊 WATCHLIST (Approaching SFPs) ━━━**\n")
            for i, coin in enumerate(watchlist, 1):
                direction_emoji = "🟢" if coin.direction == 'LONG' else "🔴"
                tv_link = self.create_tradingview_link(coin.symbol, '15m')
                description_parts.append(
                    f"**{i}. {coin.symbol}** {direction_emoji} {coin.direction}\n"
                    f"   Price: ${coin.current_price:.6f} | {coin.distance_pct:.2f}% to SFP\n"
                    f"   [Chart]({tv_link})\n"
                )

        if not description_parts:
            description_parts.append("No trades found this scan.")

        embed = {
            "title": "🎯 SFP Reversal Scanner - Best Trades",
            "description": "\n".join(description_parts),
            "color": 0x3498db,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"SFP Scanner • {self.exchange_name.upper()} • Scan every 30min"
            }
        }

        return {"embeds": [embed]}

    def format_single_trade_card(self, pick: SFPApproach, timeframe: str) -> Dict:
        """Format Discord embed card for a single best reversal trade"""
        sfp = pick.sfp
        direction_emoji = "🟢" if pick.direction == 'LONG' else "🔴"
        sfp_type = "Bullish" if sfp.is_bullish else "Bearish"

        # Determine color based on direction
        color = 0x00FF00 if pick.direction == 'LONG' else 0xFF0000  # Green for LONG, Red for SHORT

        # Format distance
        if pick.distance_pct == 0:
            distance_str = "🎯 Inside SFP Zone"
            probability = "Very High"
        elif pick.distance_pct <= 1.0:
            distance_str = f"🎯 {pick.distance_pct:.2f}% away - Very Close"
            probability = "High"
        elif pick.distance_pct <= 3.0:
            distance_str = f"📍 {pick.distance_pct:.2f}% away - Approaching"
            probability = "Medium-High"
        else:
            distance_str = f"📊 {pick.distance_pct:.2f}% away"
            probability = "Medium"

        # Format SFP range
        sfp_range = f"${sfp.bottom:.6f} - ${sfp.top:.6f}"
        sfp_size_pct = abs(sfp.top - sfp.bottom) / pick.current_price * 100

        # Format volume
        if pick.volume_24h >= 1_000_000:
            vol_str = f"${pick.volume_24h/1_000_000:.2f}M"
        else:
            vol_str = f"${pick.volume_24h/1_000:.0f}K"

        # Calculate potential move size
        if pick.direction == 'LONG':
            potential_move = ((sfp.top - pick.current_price) / pick.current_price) * 100
            entry = pick.current_price
            target1 = sfp.bottom * 1.01  # 1% above SFP bottom
            target2 = sfp.top * 0.99  # Just below SFP top
            stop_loss = pick.current_price * 0.98  # 2% below entry
        else:
            potential_move = ((pick.current_price - sfp.bottom) / pick.current_price) * 100
            entry = pick.current_price
            target1 = sfp.top * 0.99  # 1% below SFP top
            target2 = sfp.bottom * 1.01  # Just above SFP bottom
            stop_loss = pick.current_price * 1.02  # 2% above entry

        tv_link = self.create_tradingview_link(pick.symbol, timeframe)

        description = (
            f"**{direction_emoji} {pick.direction} Setup** - {probability} Probability\n\n"
            f"**Symbol:** {pick.symbol}\n"
            f"**Current Price:** ${pick.current_price:.6f}\n"
            f"**SFP Type:** {sfp_type} Gap ({sfp_range})\n"
            f"**SFP Size:** {sfp_size_pct:.2f}%\n"
            f"**Distance:** {distance_str}\n"
            f"**Volume 24h:** {vol_str}\n\n"
            f"**📈 Trade Setup:**\n"
            f"• Entry: ${entry:.6f}\n"
            f"• Target 1: ${target1:.6f} ({abs((target1-entry)/entry*100):.2f}%)\n"
            f"• Target 2: ${target2:.6f} ({abs((target2-entry)/entry*100):.2f}%)\n"
            f"• Stop Loss: ${stop_loss:.6f} ({abs((stop_loss-entry)/entry*100):.2f}%)\n"
            f"• Potential Move: {potential_move:.2f}%\n\n"
            f"[📊 View Chart]({tv_link})"
        )

        embed = {
            "title": f"🎯 Best Reversal Trade - {timeframe.upper()}",
            "description": description,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"SFP Reversal Scanner • {self.exchange_name.upper()}"
            },
            "url": tv_link
        }

        return {"embeds": [embed]}

    def send_discord_card(self, payload: Dict):
        """Send Discord card"""
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            logger.info(f"✅ Sent Discord card successfully")

        except Exception as e:
            logger.error(f"❌ Error sending Discord card: {e}")

    def run_scan(self):
        """Run a single scan cycle"""
        logger.info("🚀 Starting SFP scan cycle...")

        try:
            # Load pairs with volume filter
            self.load_pairs_with_volume()

            if not self.pairs:
                logger.warning("⚠️ No pairs to scan")
                return

            # Scan all timeframes
            trades_by_tf = {}
            all_approaches = []  # Collect all for watchlist

            for tf_key, tf_name in TIMEFRAMES.items():
                logger.info(f"📊 Scanning {tf_name} timeframe...")
                approaches = self.scan_timeframe(tf_name)
                all_approaches.extend(approaches)

                # Get 3 best trades for this timeframe (mix of LONG/SHORT, 70%+ importance)
                if approaches:
                    # Debug: show top 3 importance scores
                    top_importances = []
                    for app in approaches[:5]:  # Check top 5
                        imp = self.calculate_importance(app)
                        top_importances.append(f"{app.symbol}:{imp:.0f}%")
                    logger.info(f"   Top importance scores: {', '.join(top_importances)}")

                best_trades = self.get_best_trades(approaches, limit=3, min_importance=70.0)
                if best_trades:
                    trades_by_tf[tf_key] = best_trades
                    importance_scores = [f"{self.calculate_importance(t):.0f}%" for t in best_trades]
                    logger.info(f"✅ {tf_name}: Found {len(best_trades)} high-importance trades ({', '.join(importance_scores)})")
                else:
                    logger.info(f"ℹ️ {tf_name}: No trades with 70%+ importance found")

            # Get watchlist (2 coins approaching SFPs, 60%+ importance)
            watchlist = self.get_watchlist_coins(all_approaches, limit=2, min_importance=60.0)
            if watchlist:
                importance_scores = [f"{self.calculate_importance(c):.0f}%" for c in watchlist]
                logger.info(f"📊 Watchlist: {len(watchlist)} coins approaching SFPs ({', '.join(importance_scores)})")

            # Send single combined Discord card
            if trades_by_tf or watchlist:
                logger.info(f"📤 Sending combined Discord card...")
                payload = self.format_combined_card(trades_by_tf, watchlist)
                self.send_discord_card(payload)
                total_trades = sum(len(trades) for trades in trades_by_tf.values())
                logger.info(f"✅ Sent card with {total_trades} trades and {len(watchlist)} watchlist coins")
            else:
                logger.info("ℹ️ No trades or watchlist found this cycle - skipping Discord notification")

        except Exception as e:
            logger.error(f"❌ Error in scan cycle: {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Main loop - run scans every 30 minutes"""
        logger.info("🚀 SFP Scanner Bot started")
        logger.info(f"   Scan interval: {SCAN_INTERVAL / 60:.0f} minutes")
        logger.info(f"   Timeframes: {', '.join(TIMEFRAMES.values())}")
        logger.info(f"   Picks per TF: {PICKS_PER_TIMEFRAME}")
        logger.info(f"   Min volume: ${MIN_VOLUME_USD:,}")

        # Initialize exchange (default to Bybit)
        self.initialize_exchange()

        # Run initial scan
        self.run_scan()

        # Run periodic scans
        while True:
            try:
                logger.info(f"⏰ Waiting {SCAN_INTERVAL / 60:.0f} minutes until next scan...")
                time.sleep(SCAN_INTERVAL)
                self.run_scan()
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down...")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    # Use OKX (Bybit may be blocked in some regions)
    # Options: 'okx', 'kraken', 'bybit'
    scanner = SFPScanner(DISCORD_WEBHOOK, exchange_name='okx')
    scanner.run()
