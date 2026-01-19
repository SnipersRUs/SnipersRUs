#!/usr/bin/env python3
"""
Liquidation Scanner Bot
Scans coins for coins approaching liquidation levels on 15m, 1h, and 1d timeframes
Sends Discord alerts with colored cards:
- 15-minute: White cards
- 1-hour: Green cards
- Daily: Red cards
"""

import asyncio
import time
import logging
import requests
import numpy as np
import pandas as pd
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import ccxt
from dataclasses import dataclass

# Configuration
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1433555899019956234/WPg1bAlSEtnCDM5bxn7MaoMxhanHBd_PJL16Bigq79W6Fvp6vq_iuiubplLdqpznBj8Z"

# Exchange configurations - ONLY OKX (top 50 cryptos)
EXCHANGES = {
    'okx': {
        'class': ccxt.okx,
        'sandbox': False,
        'rateLimit': 1000,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}  # Use swap (perpetual) markets
    }
}

# Liquidation detection parameters (from Pine Script)
LIQUIDATION_PARAMS = {
    'volume_multiplier': 2.0,  # Further reduced to find more opportunities
    'volume_lookback': 50,
    'min_liquidation_size': 2.0,  # Further reduced from 3.0
    'z_score_threshold': 1.5,  # Further reduced from 1.8
    'min_importance_for_signal': 20.0,  # Further reduced from 30.0
    'max_distance_pct': 15.0  # Significantly increased to 15% to catch more approaching liquidations
}

# Timeframe configurations
TIMEFRAMES = {
    '15m': {
        'interval': '15m',
        'color': 0xFFFFFF,  # White
        'name': '15-Minute',
        'lookback_bars': 100
    },
    '1h': {
        'interval': '1h',
        'color': 0x00FF00,  # Green
        'name': '1-Hour',
        'lookback_bars': 200
    },
    '1d': {
        'interval': '1d',
        'color': 0xFF0000,  # Red
        'name': 'Daily',
        'lookback_bars': 200
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('liquidation_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """Trade record for tracking W/L"""
    trade_number: int
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    status: str  # 'PENDING', 'WIN', 'LOSS'

@dataclass
class LiquidationLevel:
    """Liquidation level data"""
    symbol: str
    exchange: str
    timeframe: str
    level: float
    type: str  # 'top' (long liquidation) or 'bottom' (short liquidation)
    importance: float
    current_price: float
    distance_pct: float
    liquidation_size: float
    timestamp: datetime
    tradingview_link: str
    is_prediction: bool = False  # True if this is a future prediction
    has_sfp: bool = False  # True if there's an SFP near this liquidation level
    sfp_info: Optional[Dict] = None  # SFP details if has_sfp is True

class LiquidationScanner:
    """Liquidation Scanner Bot"""

    def __init__(self):
        self.exchanges = {}
        self.setup_exchanges()
        self.last_daily_liquidation_sent = None  # Track when daily liquidations were last sent
        self.top_symbols_cache = {}  # {exchange: {"symbols": [...], "timestamp": datetime}}
        self.trade_counter = 1  # Trade number counter
        self.trades_history = []  # List of TradeRecord for W/L tracking

    def setup_exchanges(self):
        """Initialize exchange connections"""
        for name, config in EXCHANGES.items():
            try:
                exchange_class = config['class']
                exchange_config = {
                    'sandbox': config['sandbox'],
                    'rateLimit': config['rateLimit'],
                    'enableRateLimit': config['enableRateLimit']
                }
                if 'options' in config:
                    exchange_config['options'] = config['options']

                self.exchanges[name] = exchange_class(exchange_config)
                logger.info(f"✅ {name.upper()} exchange initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize {name.upper()}: {e}")

    async def get_current_price(self, exchange_name: str, symbol: str, fallback_price: float) -> float:
        """Get latest price from ticker; fallback to candle close if needed."""
        try:
            exchange = self.exchanges[exchange_name]
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ticker, symbol
            )
            last = ticker.get("last") or ticker.get("close")
            if last:
                return float(last)
        except Exception:
            pass
        return fallback_price

    async def get_open_interest_confirmed(self, exchange_name: str, symbol: str) -> bool:
        """Check if recent Open Interest is dropping (liquidation confirmation)."""
        try:
            exchange = self.exchanges[exchange_name]
            if not hasattr(exchange, "fetch_open_interest_history"):
                return False
            oi_data = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_open_interest_history, symbol, "1h", None, 10
            )
            if not oi_data or len(oi_data) < 2:
                return False
            latest = oi_data[-1].get("openInterest")
            previous = oi_data[-2].get("openInterest")
            if not latest or not previous:
                return False
            change_pct = (latest - previous) / previous * 100
            return change_pct <= -2.0  # OI dropped by 2%+ = liquidation confirmation
        except Exception:
            return False

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(df) < period + 1:
            return 0.0

        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        tr_list = []
        for i in range(1, len(df)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr_list.append(max(tr1, tr2, tr3))

        if len(tr_list) < period:
            return 0.0

        return np.mean(tr_list[-period:])

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    def detect_divergences(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Detect RSI and MACD divergences - returns dict with divergence info"""
        if len(df) < 30:
            return {'rsi_bullish': False, 'rsi_bearish': False, 'macd_bullish': False, 'macd_bearish': False}

        try:
            close = df['close']
            high = df['high']
            low = df['low']

            # Calculate indicators
            rsi = self.calculate_rsi(close, 14)
            macd_line, signal_line, histogram = self.calculate_macd(close)

            # Find pivot highs and lows (local maxima/minima)
            lookback = 20
            recent_highs = []
            recent_lows = []
            recent_rsi_highs = []
            recent_rsi_lows = []
            recent_macd_highs = []
            recent_macd_lows = []

            for i in range(len(df) - lookback, len(df) - 3):
                # Pivot high
                if i > 2 and i < len(df) - 3:
                    if (high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2] and
                        high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]):
                        recent_highs.append(high.iloc[i])
                        recent_rsi_highs.append(rsi.iloc[i])
                        recent_macd_highs.append(macd_line.iloc[i])

                # Pivot low
                if i > 2 and i < len(df) - 3:
                    if (low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2] and
                        low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]):
                        recent_lows.append(low.iloc[i])
                        recent_rsi_lows.append(rsi.iloc[i])
                        recent_macd_lows.append(macd_line.iloc[i])

            # Detect divergences
            rsi_bullish = False
            rsi_bearish = False
            macd_bullish = False
            macd_bearish = False

            # RSI Bullish Divergence: Lower price low, higher RSI low
            if len(recent_lows) >= 2 and len(recent_rsi_lows) >= 2:
                if (recent_lows[-1] < recent_lows[-2] and
                    recent_rsi_lows[-1] > recent_rsi_lows[-2] and
                    rsi.iloc[-1] < 45):  # RSI in oversold
                    rsi_bullish = True

            # RSI Bearish Divergence: Higher price high, lower RSI high
            if len(recent_highs) >= 2 and len(recent_rsi_highs) >= 2:
                if (recent_highs[-1] > recent_highs[-2] and
                    recent_rsi_highs[-1] < recent_rsi_highs[-2] and
                    rsi.iloc[-1] > 55):  # RSI in overbought
                    rsi_bearish = True

            # MACD Bullish Divergence: Lower price low, higher MACD low
            if len(recent_lows) >= 2 and len(recent_macd_lows) >= 2:
                if (recent_lows[-1] < recent_lows[-2] and
                    recent_macd_lows[-1] > recent_macd_lows[-2]):
                    macd_bullish = True

            # MACD Bearish Divergence: Higher price high, lower MACD high
            if len(recent_highs) >= 2 and len(recent_macd_highs) >= 2:
                if (recent_highs[-1] > recent_highs[-2] and
                    recent_macd_highs[-1] < recent_macd_highs[-2]):
                    macd_bearish = True

            return {
                'rsi_bullish': rsi_bullish,
                'rsi_bearish': rsi_bearish,
                'macd_bullish': macd_bullish,
                'macd_bearish': macd_bearish
            }
        except Exception as e:
            logger.debug(f"Error detecting divergences: {e}")
            return {'rsi_bullish': False, 'rsi_bearish': False, 'macd_bullish': False, 'macd_bearish': False}

    def detect_sweeps(self, df: pd.DataFrame, lookback: int = 36) -> Dict[str, bool]:
        """Detect liquidity sweeps that have happened OR potential sweeps in bounce"""
        if len(df) < lookback + 5:
            return {'sweep_low_happened': False, 'sweep_high_happened': False,
                   'potential_sweep_low': False, 'potential_sweep_high': False}

        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            open_price = df['open'].values
            volume = df['volume'].values

            # Calculate ATR and volume average
            atr14 = self.calculate_atr(df, 14)
            vol_avg = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)

            # Get previous extremes
            prev_low = np.min(low[-lookback:-1]) if len(low) > lookback else np.min(low[:-1])
            prev_high = np.max(high[-lookback:-1]) if len(high) > lookback else np.max(high[:-1])

            # Current candle
            current_low = low[-1]
            current_high = high[-1]
            current_close = close[-1]
            current_open = open_price[-1]
            current_volume = volume[-1]

            range_size = current_high - current_low
            body_size = abs(current_close - current_open)
            body_pct = body_size / range_size if range_size > 0 else 0

            # Detect sweeps that HAVE HAPPENED
            sweep_low_happened = False
            sweep_high_happened = False

            # Sweep low happened: price went below prev low, then closed above it
            if current_low < prev_low and current_close > prev_low:
                wick_lower = (min(current_open, current_close) - current_low) / range_size if range_size > 0 else 0
                if wick_lower >= 0.65 and body_pct <= 0.30 and current_volume > vol_avg * 1.35:
                    sweep_low_happened = True

            # Sweep high happened: price went above prev high, then closed below it
            if current_high > prev_high and current_close < prev_high:
                wick_upper = (current_high - max(current_open, current_close)) / range_size if range_size > 0 else 0
                if wick_upper >= 0.65 and body_pct <= 0.30 and current_volume > vol_avg * 1.35:
                    sweep_high_happened = True

            # Detect POTENTIAL sweeps (price approaching previous extremes)
            potential_sweep_low = False
            potential_sweep_high = False

            # Potential sweep low: price is very close to prev low, volume building
            distance_to_prev_low = abs(current_low - prev_low) / prev_low * 100 if prev_low > 0 else 999
            if distance_to_prev_low <= 0.5 and current_volume > vol_avg * 1.2:
                # Price is near previous low, volume increasing = potential sweep
                potential_sweep_low = True

            # Potential sweep high: price is very close to prev high, volume building
            distance_to_prev_high = abs(current_high - prev_high) / prev_high * 100 if prev_high > 0 else 999
            if distance_to_prev_high <= 0.5 and current_volume > vol_avg * 1.2:
                # Price is near previous high, volume increasing = potential sweep
                potential_sweep_high = True

            return {
                'sweep_low_happened': sweep_low_happened,
                'sweep_high_happened': sweep_high_happened,
                'potential_sweep_low': potential_sweep_low,
                'potential_sweep_high': potential_sweep_high
            }
        except Exception as e:
            logger.debug(f"Error detecting sweeps: {e}")
            return {'sweep_low_happened': False, 'sweep_high_happened': False,
                   'potential_sweep_low': False, 'potential_sweep_high': False}

    def detect_full_bottom_top(self, df: pd.DataFrame) -> Dict[str, bool]:
        """Detect full bottom (double/triple bottom) and full top (double/triple top) formations"""
        if len(df) < 50:
            return {'full_bottom': False, 'full_top': False}

        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values

            # Look for multiple touches of similar levels (within 1% of each other)
            lookback = 50
            recent_lows = []
            recent_highs = []

            for i in range(len(df) - lookback, len(df)):
                # Find local lows
                if i > 2 and i < len(df) - 2:
                    if (low[i] < low[i-1] and low[i] < low[i-2] and
                        low[i] < low[i+1] and low[i] < low[i+2]):
                        recent_lows.append(low[i])

                # Find local highs
                if i > 2 and i < len(df) - 2:
                    if (high[i] > high[i-1] and high[i] > high[i-2] and
                        high[i] > high[i+1] and high[i] > high[i+2]):
                        recent_highs.append(high[i])

            # Check for multiple touches of similar levels (full bottom/top)
            full_bottom = False
            full_top = False

            if len(recent_lows) >= 2:
                # Cluster lows within 1% of each other
                clustered = []
                for low_val in recent_lows:
                    found_cluster = False
                    for cluster in clustered:
                        if abs(low_val - cluster[0]) / cluster[0] <= 0.01:  # Within 1%
                            cluster.append(low_val)
                            found_cluster = True
                            break
                    if not found_cluster:
                        clustered.append([low_val])

                # Full bottom: 2+ touches of similar level
                for cluster in clustered:
                    if len(cluster) >= 2:
                        full_bottom = True
                        break

            if len(recent_highs) >= 2:
                # Cluster highs within 1% of each other
                clustered = []
                for high_val in recent_highs:
                    found_cluster = False
                    for cluster in clustered:
                        if abs(high_val - cluster[0]) / cluster[0] <= 0.01:  # Within 1%
                            cluster.append(high_val)
                            found_cluster = True
                            break
                    if not found_cluster:
                        clustered.append([high_val])

                # Full top: 2+ touches of similar level
                for cluster in clustered:
                    if len(cluster) >= 2:
                        full_top = True
                        break

            return {'full_bottom': full_bottom, 'full_top': full_top}
        except Exception as e:
            logger.debug(f"Error detecting full bottom/top: {e}")
            return {'full_bottom': False, 'full_top': False}

    def find_support_resistance_levels(self, df: pd.DataFrame, tolerance_pct: float = 0.01) -> Dict[str, List[float]]:
        """Find key support and resistance levels"""
        if len(df) < 50:
            return {'support': [], 'resistance': []}

        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values

            lookback = min(100, len(df))
            support_levels = []
            resistance_levels = []

            # Find swing lows (support) and swing highs (resistance)
            for i in range(len(df) - lookback, len(df) - 5):
                # Swing low
                if i > 2 and i < len(df) - 3:
                    if (low[i] < low[i-1] and low[i] < low[i-2] and
                        low[i] < low[i+1] and low[i] < low[i+2]):
                        support_levels.append(low[i])

                # Swing high
                if i > 2 and i < len(df) - 3:
                    if (high[i] > high[i-1] and high[i] > high[i-2] and
                        high[i] > high[i+1] and high[i] > high[i+2]):
                        resistance_levels.append(high[i])

            # Cluster similar levels
            def cluster_levels(levels, tolerance):
                if not levels:
                    return []
                sorted_levels = sorted(levels)
                clusters = []
                current_cluster = [sorted_levels[0]]

                for level in sorted_levels[1:]:
                    if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                        current_cluster.append(level)
                    else:
                        clusters.append(np.mean(current_cluster))
                        current_cluster = [level]
                if current_cluster:
                    clusters.append(np.mean(current_cluster))
                return clusters

            support_clustered = cluster_levels(support_levels, tolerance_pct)
            resistance_clustered = cluster_levels(resistance_levels, tolerance_pct)

            return {'support': support_clustered, 'resistance': resistance_clustered}
        except Exception as e:
            logger.debug(f"Error finding support/resistance: {e}")
            return {'support': [], 'resistance': []}

    def calculate_enhanced_liquidity(self, df: pd.DataFrame, lookback: int = 20) -> Dict[str, any]:
        """
        Calculate enhanced liquidity using Liquidity Hunter Scalp Pro logic
        Returns: liquidity metrics including enhanced liquidity, Z-score, and spike detection
        """
        if len(df) < lookback + 1:
            return {
                'liq_enhanced_m': 0.0,
                'z_score': 0.0,
                'is_liquidity_spike': False,
                'liq_mean': 0.0,
                'liq_std': 0.0
            }

        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values

            # Calculate liquidity (volume * range) in millions
            volume_m = volume / 1e6
            range_pu = high - low
            liq_raw_m = volume_m * range_pu

            # Enhanced liquidity with tick volume component (70% raw, 30% tick volume)
            tick_move = np.abs(close - np.roll(close, 1))
            tick_move[0] = abs(close[0] - close[1]) if len(close) > 1 else 0
            tick_volume = np.where(tick_move > 0, volume / tick_move, volume)
            tick_volume_m = tick_volume / 1e6
            liq_enhanced_m = (liq_raw_m * 0.7) + (tick_volume_m * 0.3)

            # Z-Score calculation (dynamic lookback)
            liq_mean = np.mean(liq_enhanced_m[-lookback:])
            liq_std = np.std(liq_enhanced_m[-lookback:])
            z_score = (liq_enhanced_m[-1] - liq_mean) / liq_std if liq_std > 0 else 0.0

            # Liquidity spike detection (from Pine Script: liqEnhancedM >= liqMin_val and z >= zThresh)
            liq_min_val = 1.0  # Minimum liquidity threshold (scalping mode)
            z_thresh = 1.2  # Z-score threshold
            is_liquidity_spike = liq_enhanced_m[-1] >= liq_min_val and z_score >= z_thresh

            return {
                'liq_enhanced_m': liq_enhanced_m[-1],
                'z_score': z_score,
                'is_liquidity_spike': is_liquidity_spike,
                'liq_mean': liq_mean,
                'liq_std': liq_std,
                'liq_raw_m': liq_raw_m[-1]
            }
        except Exception as e:
            logger.debug(f"Error calculating enhanced liquidity: {e}")
            return {
                'liq_enhanced_m': 0.0,
                'z_score': 0.0,
                'is_liquidity_spike': False,
                'liq_mean': 0.0,
                'liq_std': 0.0
            }

    def calculate_vwap_analysis(self, df: pd.DataFrame, multiplier: float = 1.5) -> Dict[str, any]:
        """
        Calculate VWAP deviation and extremes (from Liquidity Hunter Scalp Pro)
        Returns: VWAP value, deviation, and extreme detection
        """
        if len(df) < 20:
            return {
                'vwap_value': 0.0,
                'vwap_distance': 0.0,
                'is_vwap_extreme': False
            }

        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values

            # Calculate VWAP (Volume Weighted Average Price)
            hlc3 = (high + low + close) / 3
            vwap_value = np.sum(hlc3 * volume) / np.sum(volume) if np.sum(volume) > 0 else close[-1]

            # VWAP deviation (standard deviation of price from VWAP)
            vwap_dev = np.std(hlc3[-20:])
            vwap_distance = abs(close[-1] - vwap_value) / vwap_dev if vwap_dev > 0 else 0.0
            is_vwap_extreme = vwap_distance > multiplier

            return {
                'vwap_value': vwap_value,
                'vwap_distance': vwap_distance,
                'is_vwap_extreme': is_vwap_extreme
            }
        except Exception as e:
            logger.debug(f"Error calculating VWAP analysis: {e}")
            return {
                'vwap_value': 0.0,
                'vwap_distance': 0.0,
                'is_vwap_extreme': False
            }

    def detect_volume_absorption(self, df: pd.DataFrame, rvol_len: int = 20, rvol_min: float = 1.5) -> Dict[str, any]:
        """
        Detect volume absorption patterns (from Liquidity Hunter Scalp Pro)
        Absorption = High volume but small range (price being absorbed)
        Returns: absorption detection and relative volume
        """
        if len(df) < rvol_len + 1:
            return {
                'is_absorption': False,
                'rvol': 0.0,
                'is_high_vol': False
            }

        try:
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values

            # Calculate ATR for volatility comparison
            atr14 = self.calculate_atr(df, 14)

            # Relative volume (current volume vs average)
            avg_volume = np.mean(volume[-rvol_len:])
            rvol = volume[-1] / max(1.0, avg_volume)
            is_high_vol = rvol >= rvol_min

            # Volume absorption: high volume but small range (< 60% of ATR)
            range_pu = high[-1] - low[-1]
            absorption = is_high_vol and range_pu < atr14 * 0.6 if atr14 > 0 else False

            return {
                'is_absorption': absorption,
                'rvol': rvol,
                'is_high_vol': is_high_vol
            }
        except Exception as e:
            logger.debug(f"Error detecting volume absorption: {e}")
            return {
                'is_absorption': False,
                'rvol': 0.0,
                'is_high_vol': False
            }

    def detect_abnormal_volume(self, df: pd.DataFrame, lookback: int = 20,
                               vol_multiplier: float = 2.0, extreme_multiplier: float = 3.5) -> Dict[str, any]:
        """
        Detect abnormal and extreme volume spikes (from VPSR Pro)
        Returns: volume classification and reversal signals
        """
        if len(df) < lookback + 1:
            return {
                'is_abnormal_volume': False,
                'is_extreme_volume': False,
                'vol_ma': 0.0,
                'prev_was_extreme': False,
                'bullish_reversal': False,
                'bearish_reversal': False
            }

        try:
            volume = df['volume'].values
            close = df['close'].values
            open_price = df['open'].values

            # Volume MA (using EMA for adaptive feel)
            vol_ma = pd.Series(volume).ewm(span=lookback, adjust=False).mean().iloc[-1]

            # Standard deviation
            vol_std = np.std(volume[-lookback:])

            # Dynamic thresholds
            dynamic_threshold = vol_ma + vol_std * vol_multiplier
            extreme_threshold = vol_ma + vol_std * extreme_multiplier

            # Classifications
            current_volume = volume[-1]
            is_abnormal_volume = current_volume > dynamic_threshold
            is_extreme_volume = current_volume > extreme_threshold

            # Check if previous bar was extreme (for reversal detection)
            prev_was_extreme = False
            if len(volume) >= 2:
                prev_volume = volume[-2]
                prev_extreme_threshold = vol_ma + vol_std * extreme_multiplier
                prev_was_extreme = prev_volume > prev_extreme_threshold

            # Reversal detection: extreme volume followed by opposite candle
            current_is_bullish = close[-1] > open_price[-1]
            current_is_bearish = close[-1] < open_price[-1]
            bullish_reversal = prev_was_extreme and current_is_bullish
            bearish_reversal = prev_was_extreme and current_is_bearish

            return {
                'is_abnormal_volume': is_abnormal_volume,
                'is_extreme_volume': is_extreme_volume,
                'vol_ma': vol_ma,
                'prev_was_extreme': prev_was_extreme,
                'bullish_reversal': bullish_reversal,
                'bearish_reversal': bearish_reversal
            }
        except Exception as e:
            logger.debug(f"Error detecting abnormal volume: {e}")
            return {
                'is_abnormal_volume': False,
                'is_extreme_volume': False,
                'vol_ma': 0.0,
                'prev_was_extreme': False,
                'bullish_reversal': False,
                'bearish_reversal': False
            }

    def calculate_liquidity_divergence(self, df: pd.DataFrame, lookback: int = 10) -> Dict[str, bool]:
        """
        Detect liquidity divergence (from Liquidity Hunter Scalp Pro)
        Bearish: Price makes new high but liquidity doesn't
        Bullish: Price makes new low but liquidity doesn't
        """
        if len(df) < lookback + 1:
            return {'bearish_divergence': False, 'bullish_divergence': False}

        try:
            high = df['high'].values
            low = df['low'].values

            # Calculate enhanced liquidity for divergence
            liq_data = self.calculate_enhanced_liquidity(df, lookback)
            liq_enhanced_m = liq_data.get('liq_enhanced_m', 0.0)

            # Need to calculate liquidity for each bar (simplified - use raw liquidity)
            volume = df['volume'].values
            range_pu = high - low
            volume_m = volume / 1e6
            liq_series = volume_m * range_pu

            # Get highest/lowest price and liquidity in lookback
            highest_price = np.max(high[-lookback:])
            lowest_price = np.min(low[-lookback:])
            highest_liq = np.max(liq_series[-lookback:])

            # Current values
            current_high = high[-1]
            current_low = low[-1]
            current_liq = liq_series[-1]

            # Bearish divergence: price near high but liquidity lower
            bearish_divergence = (current_high >= highest_price * 0.995 and
                                 current_liq < highest_liq * 0.8)

            # Bullish divergence: price near low but liquidity lower
            bullish_divergence = (current_low <= lowest_price * 1.005 and
                                 current_liq < highest_liq * 0.8)

            return {
                'bearish_divergence': bearish_divergence,
                'bullish_divergence': bullish_divergence
            }
        except Exception as e:
            logger.debug(f"Error calculating liquidity divergence: {e}")
            return {'bearish_divergence': False, 'bullish_divergence': False}

    def detect_sfps_2candle(self, df: pd.DataFrame) -> List[Dict]:
        """Detect SFPs using 2-candle gap method (FVG - Fair Value Gap)"""
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
                sfps.append({
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'is_bullish': True,
                    'bar_index': i,
                    'mid': (gap_top + gap_bottom) / 2
                })

            # Bearish FVG: gap down OR small overlap (< 30% of average candle size)
            if l1 > h0 or (overlap > 0 and overlap < avg_size * 0.3 and c0 < c1):
                gap_top = max(l1, h0) if l1 > h0 else (l1 + h0) / 2
                gap_bottom = min(h0, l1)
                sfps.append({
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'is_bullish': False,
                    'bar_index': i,
                    'mid': (gap_top + gap_bottom) / 2
                })

        return sfps

    def is_sfp_filled(self, sfp: Dict, df: pd.DataFrame, current_idx: int) -> bool:
        """Check if SFP has been filled (price has moved through it)"""
        if current_idx >= len(df):
            return False

        # Check if price has moved through the gap
        for i in range(sfp['bar_index'], min(current_idx + 1, len(df))):
            low = df['low'].iloc[i]
            high = df['high'].iloc[i]

            # Filled if price has touched both top and bottom
            if low <= sfp['top'] and high >= sfp['bottom']:
                return True

        return False

    def get_active_sfps(self, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Get active (unfilled) SFPs from recent data - FOCUS ON HOURLY"""
        if len(df) < 2:
            return []

        # Only detect SFPs on hourly timeframe (they play best)
        if timeframe != '1h':
            return []

        all_sfps = self.detect_sfps_2candle(df)
        current_idx = len(df) - 1

        # Filter out filled SFPs and keep only recent ones (last 100 bars)
        active_sfps = []
        seen_levels = set()

        for sfp in all_sfps:
            # Only keep SFPs from recent bars
            if sfp['bar_index'] >= len(df) - 100:
                if not self.is_sfp_filled(sfp, df, current_idx):
                    # Check for duplicates (similar price levels)
                    level_key = (round(sfp['top'], 4), round(sfp['bottom'], 4))
                    if level_key not in seen_levels:
                        seen_levels.add(level_key)
                        sfp['timeframe'] = timeframe
                        active_sfps.append(sfp)

        # Log SFP detection for visibility
        if len(active_sfps) > 0:
            logger.info(f"🎯 SFP DETECTION: Found {len(active_sfps)} active SFPs on {timeframe} timeframe")

        return active_sfps

    def find_sfp_near_liquidation(self, liquidation_level: float, sfps: List[Dict], tolerance_pct: float = 1.5) -> Optional[Dict]:
        """Find SFP near a liquidation level (within tolerance) - increased to 1.5% for better matching"""
        best_sfp = None
        best_distance = float('inf')

        for sfp in sfps:
            sfp_mid = sfp['mid']
            # Check if liquidation level is within the SFP zone (between top and bottom)
            if sfp['bottom'] <= liquidation_level <= sfp['top']:
                # Liquidation is INSIDE the SFP zone - perfect match!
                return sfp

            # Otherwise, check distance to SFP mid
            distance_pct = abs(sfp_mid - liquidation_level) / liquidation_level * 100
            if distance_pct <= tolerance_pct and distance_pct < best_distance:
                best_distance = distance_pct
                best_sfp = sfp

        return best_sfp

    def predict_future_liquidations(self, df: pd.DataFrame, symbol: str, exchange: str, timeframe: str) -> List[Dict]:
        """PREDICT future liquidations BEFORE they happen - looking into the future"""
        if df is None or len(df) < 100:
            return []

        predictions = []
        current_price = df['close'].iloc[-1]
        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values

        # Calculate volume statistics
        volume_lookback = 50
        avg_volume = np.mean(volume[-volume_lookback:])
        volume_std = np.std(volume[-volume_lookback:])
        current_volume = volume[-1]
        volume_z = (current_volume - avg_volume) / volume_std if volume_std > 0 else 0.0

        # Calculate ATR for volatility
        atr14 = self.calculate_atr(df, 14)

        # Find support/resistance levels (areas where price has bounced before - likely liquidation zones)
        lookback = min(100, len(df))
        support_levels = []
        resistance_levels = []

        # Find recent swing lows (support) and swing highs (resistance)
        for i in range(len(df) - lookback, len(df) - 5):
            # Swing low (support) - local minimum
            if i > 2 and i < len(df) - 3:
                is_swing_low = (low[i] < low[i-1] and low[i] < low[i-2] and
                               low[i] < low[i+1] and low[i] < low[i+2])
                if is_swing_low:
                    support_levels.append(low[i])

            # Swing high (resistance) - local maximum
            if i > 2 and i < len(df) - 3:
                is_swing_high = (high[i] > high[i-1] and high[i] > high[i-2] and
                                high[i] > high[i+1] and high[i] > high[i+2])
                if is_swing_high:
                    resistance_levels.append(high[i])

        # Cluster similar levels together (within 0.5% of each other)
        def cluster_levels(levels, tolerance_pct=0.005):
            if not levels:
                return []
            levels_sorted = sorted(levels)
            clusters = []
            current_cluster = [levels_sorted[0]]

            for level in levels_sorted[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance_pct:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]
            if current_cluster:
                clusters.append(np.mean(current_cluster))
            return clusters

        support_clusters = cluster_levels(support_levels)
        resistance_clusters = cluster_levels(resistance_levels)

        # Check if price is approaching these levels with increasing volume
        for support in support_clusters:
            distance_pct = abs(current_price - support) / current_price * 100 if current_price > 0 else 999

            # Only predict if price is within 3% of support and approaching
            if 0.1 <= distance_pct <= 3.0 and current_price > support:
                # Check for volume buildup
                recent_volume_avg = np.mean(volume[-5:])
                prev_volume_avg = np.mean(volume[-15:-5]) if len(volume) >= 15 else recent_volume_avg
                volume_increasing = recent_volume_avg > prev_volume_avg * 1.2

                # Check for price compression (low volatility before breakout)
                recent_atr = np.mean([high[i] - low[i] for i in range(-5, 0)])
                compression = recent_atr < atr14 * 0.7 if atr14 > 0 else False

                # Calculate prediction confidence
                confidence = 0.0
                if volume_increasing:
                    confidence += 30.0
                if compression:
                    confidence += 20.0
                if volume_z >= 1.5:
                    confidence += 25.0
                if distance_pct <= 1.0:
                    confidence += 25.0  # Very close = higher confidence

                if confidence >= 40.0:  # Minimum confidence threshold
                    predictions.append({
                        "level": support,
                        "type": "bottom",  # Support = potential short liquidation (bounce up)
                        "importance": min(100.0, confidence),
                        "distance_pct": distance_pct,
                        "prediction_type": "FUTURE",  # Mark as prediction
                        "volume_trend": "increasing" if volume_increasing else "stable",
                        "compression": compression
                    })

        for resistance in resistance_clusters:
            distance_pct = abs(current_price - resistance) / current_price * 100 if current_price > 0 else 999

            # Only predict if price is within 3% of resistance and approaching
            if 0.1 <= distance_pct <= 3.0 and current_price < resistance:
                # Check for volume buildup
                recent_volume_avg = np.mean(volume[-5:])
                prev_volume_avg = np.mean(volume[-15:-5]) if len(volume) >= 15 else recent_volume_avg
                volume_increasing = recent_volume_avg > prev_volume_avg * 1.2

                # Check for price compression
                recent_atr = np.mean([high[i] - low[i] for i in range(-5, 0)])
                compression = recent_atr < atr14 * 0.7 if atr14 > 0 else False

                # Calculate prediction confidence
                confidence = 0.0
                if volume_increasing:
                    confidence += 30.0
                if compression:
                    confidence += 20.0
                if volume_z >= 1.5:
                    confidence += 25.0
                if distance_pct <= 1.0:
                    confidence += 25.0

                if confidence >= 40.0:
                    predictions.append({
                        "level": resistance,
                        "type": "top",  # Resistance = potential long liquidation (bounce down)
                        "importance": min(100.0, confidence),
                        "distance_pct": distance_pct,
                        "prediction_type": "FUTURE",
                        "volume_trend": "increasing" if volume_increasing else "stable",
                        "compression": compression
                    })

        return predictions

    def detect_liquidation_levels(self, df: pd.DataFrame, symbol: str, exchange: str, timeframe: str) -> List[Dict]:
        """Detect liquidation levels from OHLCV data using Pine Script logic + PREDICT future ones"""
        if df is None or len(df) < LIQUIDATION_PARAMS['volume_lookback']:
            return []

        liquidations = []

        # FIRST: Predict future liquidations (looking ahead)
        future_predictions = self.predict_future_liquidations(df, symbol, exchange, timeframe)
        for pred in future_predictions:
            liquidations.append({
                "level": pred["level"],
                "importance": pred["importance"],
                "type": pred["type"],
                "liquidation_size": 0.0,  # Unknown for predictions
                "volume_z": 0.0,
                "liquidation_z": 0.0,
                "timestamp": df['timestamp'].iloc[-1],  # Current time
                "candle_index": len(df) - 1,
                "prediction_type": "FUTURE",  # Mark as prediction
                "distance_pct": pred["distance_pct"]
            })
        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values

        # Calculate volume statistics
        volume_lookback = LIQUIDATION_PARAMS['volume_lookback']
        avg_volume = np.mean(volume[-volume_lookback:])
        volume_std = np.std(volume[-volume_lookback:])

        # Calculate ATR
        atr14 = self.calculate_atr(df, 14)

        # Check recent candles for liquidations
        lookback_window = min(50, len(df) - volume_lookback)
        start_idx = max(volume_lookback, len(df) - lookback_window)

        for i in range(start_idx, len(df)):
            try:
                candle_high = high[i]
                candle_low = low[i]
                candle_close = close[i]
                candle_open = open_price[i]
                candle_volume = volume[i]

                # Volume analysis
                volume_z = (candle_volume - avg_volume) / volume_std if volume_std > 0 else 0.0
                abnormal_volume = volume_z >= LIQUIDATION_PARAMS['z_score_threshold']
                very_abnormal_volume = volume_z >= (LIQUIDATION_PARAMS['z_score_threshold'] * 1.5)

                # Liquidation size calculation
                range_pu = candle_high - candle_low
                volume_m = candle_volume / 1e6
                liquidation_size = volume_m * range_pu

                # Average liquidation size for comparison
                liquidation_sizes = []
                for j in range(max(0, i - volume_lookback), i):
                    rng = high[j] - low[j]
                    vol_m = volume[j] / 1e6
                    liquidation_sizes.append(vol_m * rng)

                avg_liquidation_size = np.mean(liquidation_sizes) if liquidation_sizes else 0
                liquidation_std = np.std(liquidation_sizes) if len(liquidation_sizes) > 1 else 1
                liquidation_z = (liquidation_size - avg_liquidation_size) / liquidation_std if liquidation_std > 0 else 0.0

                # Major liquidation detection - be more lenient
                is_major_liquidation = (liquidation_size >= LIQUIDATION_PARAMS['min_liquidation_size']) or \
                                       (abnormal_volume and liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold'] * 0.6) or \
                                       very_abnormal_volume or \
                                       (candle_volume > avg_volume * LIQUIDATION_PARAMS['volume_multiplier'] and range_pu > atr14 * 1.2)

                if not is_major_liquidation:
                    continue

                # Calculate importance score (0-100)
                importance = 0.0

                # Volume component (0-40 points)
                if very_abnormal_volume:
                    importance += 40.0
                elif abnormal_volume:
                    importance += 25.0
                elif candle_volume > avg_volume * LIQUIDATION_PARAMS['volume_multiplier']:
                    importance += 10.0

                # Liquidation size component (0-30 points)
                if liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold'] * 1.5:
                    importance += 30.0
                elif liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold']:
                    importance += 20.0
                elif liquidation_size >= LIQUIDATION_PARAMS['min_liquidation_size']:
                    importance += 10.0

                # Price range component (0-20 points)
                if atr14 > 0:
                    range_ratio = range_pu / atr14
                    if range_ratio > 3.0:
                        importance += 20.0
                    elif range_ratio > 2.0:
                        importance += 15.0
                    elif range_ratio > 1.5:
                        importance += 10.0

                # Wick rejection component (0-10 points)
                if range_pu > 0:
                    wick_size = (candle_high - max(candle_close, candle_open)) + (min(candle_close, candle_open) - candle_low)
                    wick_ratio = wick_size / range_pu
                    if wick_ratio > 0.6:
                        importance += 10.0
                    elif wick_ratio > 0.4:
                        importance += 5.0

                importance = min(100.0, importance)

                # Only track significant liquidations - be very lenient now
                min_importance = LIQUIDATION_PARAMS['min_importance_for_signal']
                # Lower threshold for various conditions
                if very_abnormal_volume:
                    min_importance = min_importance * 0.5
                elif abnormal_volume:
                    min_importance = min_importance * 0.7
                elif liquidation_size >= LIQUIDATION_PARAMS['min_liquidation_size'] * 1.5:
                    min_importance = min_importance * 0.8

                if importance < min_importance:
                    continue

                # Determine liquidation level and type
                is_bearish_candle = candle_close < candle_open
                if is_bearish_candle:
                    # Bearish liquidation - likely cleared longs (wick above) = TOP liquidation
                    liq_level = candle_high
                    liq_type = "top"  # Longs got liquidated at top
                else:
                    # Bullish liquidation - likely cleared shorts (wick below) = BOTTOM liquidation
                    liq_level = candle_low
                    liq_type = "bottom"  # Shorts got liquidated at bottom

                # Get timestamp
                liq_timestamp = df['timestamp'].iloc[i]

                liquidations.append({
                    "level": liq_level,
                    "importance": importance,
                    "type": liq_type,
                    "liquidation_size": liquidation_size,
                    "volume_z": volume_z,
                    "liquidation_z": liquidation_z,
                    "timestamp": liq_timestamp,
                    "candle_index": i
                })

            except Exception as e:
                continue

        # Sort by importance (highest first)
        liquidations.sort(key=lambda x: x["importance"], reverse=True)
        return liquidations

    async def get_symbols(self, exchange_name: str, limit: int = None) -> List[str]:
        """Get trading symbols from exchange - Kraken, OKX, and Bybit"""
        try:
            exchange = self.exchanges[exchange_name]
            markets = await asyncio.get_event_loop().run_in_executor(
                None, exchange.load_markets
            )

            symbols = []
            for symbol, market in markets.items():
                if exchange_name == 'kraken':
                    # Kraken: Skip for now - futures have low liquidity and different format
                    # Kraken futures use different symbol formats and are less liquid
                    continue
                elif exchange_name == 'okx':
                    # OKX: Get perpetual swaps - accept any non-spot USDT market
                    is_active = market.get('active', True)
                    if not is_active:
                        continue

                    market_type = market.get('type', '').lower()
                    quote = market.get('quote', '').upper()
                    symbol_upper = symbol.upper()

                    # Skip spot markets
                    if market_type == 'spot':
                        continue

                    # Accept any USDT pair that's not spot (swap, future, etc.)
                    is_usdt_pair = (quote == 'USDT' or 'USDT' in symbol_upper)

                    if is_usdt_pair:
                        symbols.append(symbol)
                elif exchange_name == 'bybit':
                    # Bybit: Get perpetual swaps - check for swap/contract type AND linear AND USDT
                    is_active = market.get('active', True)
                    market_type = market.get('type', '')
                    is_swap = market.get('swap', False)
                    is_linear = market.get('linear', False)
                    quote = market.get('quote', '')

                    # Bybit perpetuals: type in ['swap', 'contract'], linear=True, quote='USDT'
                    if (is_active and
                        (market_type in ['swap', 'contract'] or is_swap) and
                        (is_linear or quote == 'USDT') and
                        (quote == 'USDT' or 'USDT' in symbol)):
                        symbols.append(symbol)
                else:
                    # Fallback for other exchanges
                    if (market.get('quote') == 'USDT' and
                        market.get('active', True) and
                        market.get('type') in ['future', 'swap', 'spot'] and
                        'USDT' in symbol):
                        symbols.append(symbol)

            # Log what we found for debugging
            if len(symbols) == 0 and exchange_name in ['okx', 'bybit', 'kraken']:
                logger.info(f"⚠️ {exchange_name.upper()}: No symbols found. Total markets: {len(markets)}")
                # Log sample markets to see structure
                sample_count = 0
                usdt_count = 0
                for sym, mkt in markets.items():
                    if 'USDT' in sym.upper():
                        usdt_count += 1
                        if sample_count < 5:
                            logger.info(f"   Sample: {sym} - type: {mkt.get('type')}, swap: {mkt.get('swap')}, linear: {mkt.get('linear')}, quote: {mkt.get('quote')}, active: {mkt.get('active')}")
                            sample_count += 1
                logger.info(f"   Found {usdt_count} markets with USDT in symbol")

            # Apply limit if specified
            if limit:
                return symbols[:limit]
            return symbols

        except Exception as e:
            logger.error(f"Error getting symbols from {exchange_name}: {e}")
            return []

    async def get_top_volume_symbols(self, exchange_name: str, symbols: List[str], limit: int = 50) -> List[str]:
        """Get top volume symbols from list with 24h cache"""
        try:
            cache_entry = self.top_symbols_cache.get(exchange_name)
            if cache_entry:
                age_seconds = (datetime.now(timezone.utc) - cache_entry["timestamp"]).total_seconds()
                if age_seconds < 24 * 3600:
                    return cache_entry["symbols"][:limit]

            exchange = self.exchanges[exchange_name]
            tickers = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_tickers
            )

            symbol_volumes = []
            for symbol in symbols:
                ticker = tickers.get(symbol, {})
                volume = ticker.get('quoteVolume', 0) or ticker.get('baseVolume', 0) or 0
                if volume > 0:
                    symbol_volumes.append((symbol, volume))

            # Sort by volume descending
            symbol_volumes.sort(key=lambda x: x[1], reverse=True)

            # Return TOP 50 cryptos
            top_50 = [s[0] for s in symbol_volumes[:limit]]
            self.top_symbols_cache[exchange_name] = {
                "symbols": top_50,
                "timestamp": datetime.now(timezone.utc)
            }
            logger.info(f"📊 Top {len(top_50)} cryptos by volume: {', '.join([s.split('/')[0] if '/' in s else s.split(':')[0] for s in top_50[:5]])}...")
            return top_50

        except Exception as e:
            logger.error(f"Error getting top volume symbols: {e}")
            # Fallback to first N symbols
            return symbols[:limit]

    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
        """Get OHLCV data from exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            ohlcv = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ohlcv, symbol, timeframe, None, limit
            )

            if not ohlcv or len(ohlcv) == 0:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except Exception as e:
            logger.debug(f"Error getting OHLCV for {symbol} on {exchange_name}: {e}")
            return None

    def get_tradingview_link(self, symbol: str, exchange: str) -> str:
        """Generate TradingView link for symbol"""
        # Clean symbol format
        base_symbol = symbol.split('/')[0] if '/' in symbol else symbol

        # Remove :USDT suffix if present for cleaner symbol
        clean_symbol = symbol.replace(':USDT', '').replace(':USD', '')

        if exchange == 'kraken':
            # Kraken format: KRAKEN:BTCUSD
            tv_symbol = clean_symbol.replace('/', '')
            return f"https://www.tradingview.com/chart/?symbol=KRAKEN:{tv_symbol}"
        elif exchange == 'okx':
            # OKX format: OKX:BTCUSDT.P (perpetual) or OKX:BTCUSDT (spot)
            if ':USDT' in symbol or '/USDT' in symbol:
                tv_symbol = clean_symbol.replace('/', '') + '.P'
            else:
                tv_symbol = clean_symbol.replace('/', '')
            return f"https://www.tradingview.com/chart/?symbol=OKX:{tv_symbol}"
        elif exchange == 'bybit':
            # Bybit format: BYBIT:BTCUSDT
            tv_symbol = clean_symbol.replace('/', '')
            return f"https://www.tradingview.com/chart/?symbol=BYBIT:{tv_symbol}"
        else:
            return f"https://www.tradingview.com/chart/?symbol={exchange.upper()}:{clean_symbol.replace('/', '')}"

    async def scan_symbol_timeframe(self, exchange_name: str, symbol: str, timeframe_key: str) -> List[LiquidationLevel]:
        """Scan single symbol on single timeframe for approaching liquidations"""
        levels = []

        try:
            timeframe_config = TIMEFRAMES[timeframe_key]
            df = await self.get_ohlcv(
                exchange_name,
                symbol,
                timeframe_config['interval'],
                timeframe_config['lookback_bars']
            )

            if df is None or len(df) < LIQUIDATION_PARAMS['volume_lookback']:
                return []

            # Detect liquidation levels
            liquidations = self.detect_liquidation_levels(df, symbol, exchange_name, timeframe_key)

            if not liquidations:
                return []

            # Get current price - prefer live ticker for accuracy
            current_price = await self.get_current_price(
                exchange_name, symbol, df['close'].iloc[-1]
            )

            # Open Interest confirmation (filters fake volume spikes)
            oi_confirmed = await self.get_open_interest_confirmed(exchange_name, symbol)

            # Detect divergences, full bottoms/tops, sweeps, and SFPs for importance boosting
            divergences = self.detect_divergences(df)
            full_formations = self.detect_full_bottom_top(df)
            sr_levels = self.find_support_resistance_levels(df)
            sweeps = self.detect_sweeps(df)
            # Get active SFPs (FOCUS ON HOURLY - they play best!)
            active_sfps = self.get_active_sfps(df, timeframe_key)

            # Enhanced liquidity and volume analysis (from Liquidity Hunter Scalp Pro & VPSR Pro)
            liq_data = self.calculate_enhanced_liquidity(df, lookback=20)
            vwap_data = self.calculate_vwap_analysis(df, multiplier=1.5)
            absorption_data = self.detect_volume_absorption(df, rvol_len=20, rvol_min=1.5)
            abnormal_vol_data = self.detect_abnormal_volume(df, lookback=20, vol_multiplier=2.0, extreme_multiplier=3.5)
            liq_divergence = self.calculate_liquidity_divergence(df, lookback=10)
            if len(active_sfps) > 0:
                logger.info(f"🎯 {symbol} ({timeframe_key}): Found {len(active_sfps)} active SFPs - checking for SFP + liquidation combos...")

            # Log when we find liquidations (INFO level so we can see it)
            logger.info(f"🔍 {symbol} ({timeframe_key}): Detected {len(liquidations)} liquidation(s) - checking distance...")
            logger.info(f"💰 {symbol} ({timeframe_key}): Current price: ${current_price:.4f}, checking {len(liquidations)} liquidations")

            # Check distance to liquidation levels and detect if fully swept
            # PRIORITIZE FUTURE PREDICTIONS (they're more valuable - looking ahead!)
            future_predictions = [l for l in liquidations if l.get('prediction_type') == 'FUTURE']
            past_liquidations = [l for l in liquidations if l.get('prediction_type') != 'FUTURE']

            # Process future predictions FIRST (they're looking ahead!)
            for liq in future_predictions:
                liq_level = liq['level']
                distance_pct = liq.get('distance_pct', abs(current_price - liq_level) / current_price * 100 if current_price > 0 else 999)

                # Future predictions are already within range (0.1-3%), so include them
                max_dist = 3.0  # Future predictions are within 3%

                if distance_pct <= max_dist:
                    # Check for SFP near liquidation level (SFP + liquidation = ultimate entry!)
                    sfp_near = self.find_sfp_near_liquidation(liq_level, active_sfps, tolerance_pct=1.0)
                    has_sfp = sfp_near is not None

                    # Boost importance for predictions based on divergences, support/resistance, full formations, SWEEPS, and SFPs
                    boosted_importance = liq['importance'] + 10.0  # Base boost for being a prediction

                    # MASSIVE BOOST for SFP + liquidation combo (ultimate top/bottom entry!)
                    if has_sfp:
                        boosted_importance += 30.0  # HUGE boost for SFP + liquidation combo
                        logger.info(f"🎯 SFP + LIQUIDATION COMBO: {symbol} - {liq['type'].upper()} at ${liq_level:.4f} with SFP at ${sfp_near['mid']:.4f}")

                    # MAJOR BOOST for 1h potential sweeps (PRIORITY!)
                    is_1h_potential_sweep = False
                    if timeframe_key == '1h':
                        if liq['type'] == 'bottom' and sweeps['potential_sweep_low']:
                            boosted_importance += 25.0  # HUGE boost for 1h potential sweep low
                            is_1h_potential_sweep = True
                        elif liq['type'] == 'top' and sweeps['potential_sweep_high']:
                            boosted_importance += 25.0  # HUGE boost for 1h potential sweep high
                            is_1h_potential_sweep = True

                    # Boost for sweeps that have happened
                    if liq['type'] == 'bottom' and sweeps['sweep_low_happened']:
                        boosted_importance += 20.0  # Sweep happened = high reversal probability
                    elif liq['type'] == 'top' and sweeps['sweep_high_happened']:
                        boosted_importance += 20.0  # Sweep happened = high reversal probability

                    # Check if prediction is at support/resistance level
                    is_at_sr = False
                    if liq['type'] == 'bottom':
                        # Bottom prediction - check if near support
                        for support in sr_levels['support']:
                            if abs(liq_level - support) / support <= 0.01:  # Within 1%
                                is_at_sr = True
                                boosted_importance += 15.0  # Major boost for support alignment
                                break
                    else:  # top
                        # Top prediction - check if near resistance
                        for resistance in sr_levels['resistance']:
                            if abs(liq_level - resistance) / resistance <= 0.01:  # Within 1%
                                is_at_sr = True
                                boosted_importance += 15.0  # Major boost for resistance alignment
                                break

                    # Boost for divergences matching prediction type
                    if liq['type'] == 'bottom':
                        # Bottom prediction + bullish divergence = strong reversal setup
                        if divergences['rsi_bullish']:
                            boosted_importance += 10.0
                        if divergences['macd_bullish']:
                            boosted_importance += 10.0
                        if full_formations['full_bottom']:
                            boosted_importance += 15.0  # Full bottom formation
                        # Liquidity divergence (from Liquidity Hunter)
                        if liq_divergence['bullish_divergence']:
                            boosted_importance += 12.0
                    else:  # top
                        # Top prediction + bearish divergence = strong reversal setup
                        if divergences['rsi_bearish']:
                            boosted_importance += 10.0
                        if divergences['macd_bearish']:
                            boosted_importance += 10.0
                        if full_formations['full_top']:
                            boosted_importance += 15.0  # Full top formation
                        # Liquidity divergence (from Liquidity Hunter)
                        if liq_divergence['bearish_divergence']:
                            boosted_importance += 12.0

                    # Enhanced liquidity spike boost (from Liquidity Hunter Scalp Pro)
                    if liq_data['is_liquidity_spike']:
                        boosted_importance += 8.0  # Base liquidity spike
                        if liq_data['z_score'] >= 2.0:  # Strong Z-score
                            boosted_importance += 5.0

                    # VWAP extreme boost (price far from VWAP = reversal potential)
                    if vwap_data['is_vwap_extreme']:
                        boosted_importance += 6.0

                    # Volume absorption boost (high volume, small range = absorption)
                    if absorption_data['is_absorption']:
                        boosted_importance += 10.0

                    # Abnormal/extreme volume boost (from VPSR Pro)
                    if abnormal_vol_data['is_extreme_volume']:
                        boosted_importance += 12.0  # Extreme volume = major event
                    elif abnormal_vol_data['is_abnormal_volume']:
                        boosted_importance += 6.0  # Abnormal volume = significant

                    # Reversal signal boost (extreme volume followed by reversal candle)
                    if liq['type'] == 'bottom' and abnormal_vol_data['bullish_reversal']:
                        boosted_importance += 15.0  # Bullish reversal after extreme volume
                    elif liq['type'] == 'top' and abnormal_vol_data['bearish_reversal']:
                        boosted_importance += 15.0  # Bearish reversal after extreme volume

                    if not oi_confirmed:
                        boosted_importance -= 10.0  # Degrade if OI doesn't confirm
                    boosted_importance = min(100.0, max(0.0, boosted_importance))  # Cap at 0-100

                    # Log sweep detection
                    if is_1h_potential_sweep:
                        logger.info(f"🔥 1H POTENTIAL SWEEP PREDICTION: {symbol} - {liq['type'].upper()} at ${liq_level:.4f}")

                    logger.info(f"🔮 FUTURE PREDICTION: {symbol} ({timeframe_key}): Predicted liquidation at ${liq_level:.4f}, distance: {distance_pct:.2f}%, importance: {boosted_importance:.1f}% (boosted from {liq['importance']:.1f}%)")
                    tradingview_link = self.get_tradingview_link(symbol, exchange_name)

                    levels.append(LiquidationLevel(
                        symbol=symbol,
                        exchange=exchange_name,
                        timeframe=timeframe_key,
                        level=liq_level,
                        type=liq['type'],
                        importance=boosted_importance,
                        current_price=current_price,
                        distance_pct=distance_pct,
                        liquidation_size=liq.get('liquidation_size', 0.0),
                        timestamp=liq['timestamp'],
                        tradingview_link=tradingview_link,
                        is_prediction=True,  # Mark as future prediction
                        has_sfp=has_sfp,
                        sfp_info=sfp_near
                    ))

            # Then process past liquidations (already happened)
            for liq in past_liquidations:
                liq_level = liq['level']
                distance_pct = abs(current_price - liq_level) / current_price * 100 if current_price > 0 else 999

                # Check if liquidation has been FULLY SWEPT (price has touched/passed the level)
                # For 1h timeframes, we want reversals AFTER the sweep
                is_fully_swept = False
                if timeframe_key == '1h':
                    # Check if price has touched or passed the liquidation level in recent candles
                    # Look at last 5 candles to see if liquidation was swept
                    recent_candles = df.tail(5)
                    if liq['type'] == 'bottom':
                        # Bottom liquidation swept if price went below the level
                        is_fully_swept = (recent_candles['low'].min() <= liq_level * 1.001)  # 0.1% tolerance
                    else:  # top
                        # Top liquidation swept if price went above the level
                        is_fully_swept = (recent_candles['high'].max() >= liq_level * 0.999)  # 0.1% tolerance

                    # For best trade opportunities, we ONLY want fully swept hourly liquidations
                    # Price should have swept and now be reversing
                    if is_fully_swept:
                        # Check if price is now reversing (moved away from the swept level)
                        if liq['type'] == 'bottom':
                            # Bottom swept - price should be above the level now (reversal up)
                            is_reversing = current_price > liq_level * 1.002  # 0.2% above for reversal confirmation
                        else:  # top
                            # Top swept - price should be below the level now (reversal down)
                            is_reversing = current_price < liq_level * 0.998  # 0.2% below for reversal confirmation

                        if not is_reversing:
                            logger.debug(f"⏳ {symbol} ({timeframe_key}): Liquidation swept but not yet reversing")
                            continue  # Skip if swept but not reversing yet

                # Only alert if within max distance
                # For daily timeframe, allow further distance (22.5% vs 15%)
                # For 1h, allow slightly more (18% vs 15%)
                if timeframe_key == '1d':
                    max_dist = LIQUIDATION_PARAMS['max_distance_pct'] * 1.5
                elif timeframe_key == '1h':
                    max_dist = LIQUIDATION_PARAMS['max_distance_pct'] * 1.2
                else:
                    max_dist = LIQUIDATION_PARAMS['max_distance_pct']

                # Log first few to see what's happening
                if past_liquidations.index(liq) < 3:
                    sweep_status = "SWEPT ✅" if is_fully_swept else "APPROACHING"
                    logger.info(f"📏 {symbol} ({timeframe_key}): Liq ${liq_level:.4f}, distance: {distance_pct:.2f}%, max: {max_dist:.2f}%, importance: {liq['importance']:.1f}%, {sweep_status}")

                if distance_pct <= max_dist:
                    # Check for SFP near liquidation level (SFP + liquidation = ultimate entry!)
                    sfp_near = self.find_sfp_near_liquidation(liq_level, active_sfps, tolerance_pct=1.0)
                    has_sfp = sfp_near is not None

                    # Boost importance based on divergences, support/resistance, full formations, SWEEPS, and SFPs
                    boosted_importance = liq['importance']

                    # MASSIVE BOOST for SFP + liquidation combo (ultimate top/bottom entry!)
                    if has_sfp:
                        boosted_importance += 30.0  # HUGE boost for SFP + liquidation combo
                        logger.info(f"🎯 SFP + LIQUIDATION COMBO: {symbol} - {liq['type'].upper()} at ${liq_level:.4f} with SFP at ${sfp_near['mid']:.4f}")

                    # MAJOR BOOST for 1h potential sweeps (PRIORITY!)
                    is_1h_potential_sweep = False
                    if timeframe_key == '1h':
                        if liq['type'] == 'bottom' and sweeps['potential_sweep_low']:
                            boosted_importance += 25.0  # HUGE boost for 1h potential sweep low
                            is_1h_potential_sweep = True
                        elif liq['type'] == 'top' and sweeps['potential_sweep_high']:
                            boosted_importance += 25.0  # HUGE boost for 1h potential sweep high
                            is_1h_potential_sweep = True

                    # Boost for sweeps that have happened
                    if liq['type'] == 'bottom' and sweeps['sweep_low_happened']:
                        boosted_importance += 20.0  # Sweep happened = high reversal probability
                    elif liq['type'] == 'top' and sweeps['sweep_high_happened']:
                        boosted_importance += 20.0  # Sweep happened = high reversal probability

                    # Check if liquidation is at support/resistance level
                    is_at_sr = False
                    if liq['type'] == 'bottom':
                        # Bottom liquidation - check if near support
                        for support in sr_levels['support']:
                            if abs(liq_level - support) / support <= 0.01:  # Within 1%
                                is_at_sr = True
                                boosted_importance += 15.0  # Major boost for support alignment
                                break
                    else:  # top
                        # Top liquidation - check if near resistance
                        for resistance in sr_levels['resistance']:
                            if abs(liq_level - resistance) / resistance <= 0.01:  # Within 1%
                                is_at_sr = True
                                boosted_importance += 15.0  # Major boost for resistance alignment
                                break

                    # Boost for divergences matching liquidation type
                    if liq['type'] == 'bottom':
                        # Bottom liquidation + bullish divergence = strong reversal setup
                        if divergences['rsi_bullish']:
                            boosted_importance += 10.0
                        if divergences['macd_bullish']:
                            boosted_importance += 10.0
                        if full_formations['full_bottom']:
                            boosted_importance += 15.0  # Full bottom formation
                        # Liquidity divergence (from Liquidity Hunter)
                        if liq_divergence['bullish_divergence']:
                            boosted_importance += 12.0
                    else:  # top
                        # Top liquidation + bearish divergence = strong reversal setup
                        if divergences['rsi_bearish']:
                            boosted_importance += 10.0
                        if divergences['macd_bearish']:
                            boosted_importance += 10.0
                        if full_formations['full_top']:
                            boosted_importance += 15.0  # Full top formation
                        # Liquidity divergence (from Liquidity Hunter)
                        if liq_divergence['bearish_divergence']:
                            boosted_importance += 12.0

                    # Enhanced liquidity spike boost (from Liquidity Hunter Scalp Pro)
                    if liq_data['is_liquidity_spike']:
                        boosted_importance += 8.0  # Base liquidity spike
                        if liq_data['z_score'] >= 2.0:  # Strong Z-score
                            boosted_importance += 5.0

                    # VWAP extreme boost (price far from VWAP = reversal potential)
                    if vwap_data['is_vwap_extreme']:
                        boosted_importance += 6.0

                    # Volume absorption boost (high volume, small range = absorption)
                    if absorption_data['is_absorption']:
                        boosted_importance += 10.0

                    # Abnormal/extreme volume boost (from VPSR Pro)
                    if abnormal_vol_data['is_extreme_volume']:
                        boosted_importance += 12.0  # Extreme volume = major event
                    elif abnormal_vol_data['is_abnormal_volume']:
                        boosted_importance += 6.0  # Abnormal volume = significant

                    # Reversal signal boost (extreme volume followed by reversal candle)
                    if liq['type'] == 'bottom' and abnormal_vol_data['bullish_reversal']:
                        boosted_importance += 15.0  # Bullish reversal after extreme volume
                    elif liq['type'] == 'top' and abnormal_vol_data['bearish_reversal']:
                        boosted_importance += 15.0  # Bearish reversal after extreme volume

                    if not oi_confirmed:
                        boosted_importance -= 15.0  # Degrade if OI doesn't confirm
                    boosted_importance = min(100.0, max(0.0, boosted_importance))  # Cap at 0-100

                    # Log sweep detection
                    if is_1h_potential_sweep:
                        logger.info(f"🔥 1H POTENTIAL SWEEP DETECTED: {symbol} - {liq['type'].upper()} at ${liq_level:.4f}")
                    elif (liq['type'] == 'bottom' and sweeps['sweep_low_happened']) or (liq['type'] == 'top' and sweeps['sweep_high_happened']):
                        logger.info(f"✅ SWEEP HAPPENED: {symbol} - {liq['type'].upper()} at ${liq_level:.4f}")

                    logger.info(f"✅ {symbol} ({timeframe_key}): Adding liquidation at ${liq_level:.4f}, distance: {distance_pct:.2f}%, importance: {boosted_importance:.1f}% (boosted from {liq['importance']:.1f}%)")
                    tradingview_link = self.get_tradingview_link(symbol, exchange_name)

                    levels.append(LiquidationLevel(
                        symbol=symbol,
                        exchange=exchange_name,
                        timeframe=timeframe_key,
                        level=liq_level,
                        type=liq['type'],
                        importance=boosted_importance,
                        current_price=current_price,
                        distance_pct=distance_pct,
                        liquidation_size=liq['liquidation_size'],
                        timestamp=liq['timestamp'],
                        tradingview_link=tradingview_link,
                        is_prediction=False,  # Past liquidation, not a prediction
                        has_sfp=has_sfp,
                        sfp_info=sfp_near
                    ))

        except Exception as e:
            logger.debug(f"Error scanning {symbol} {timeframe_key} on {exchange_name}: {e}")

        return levels

    async def scan_exchange(self, exchange_name: str) -> List[LiquidationLevel]:
        """Scan single exchange for approaching liquidations"""
        logger.info(f"🔍 Scanning {exchange_name.upper()}...")
        all_levels = []

        try:
            # Get top volume symbols for all exchanges - ONLY TOP 10 CRYPTOS
            all_symbols = await self.get_symbols(exchange_name, limit=None)
            # Get top 10 by volume - focus on highest liquidity cryptos
            symbols = await self.get_top_volume_symbols(exchange_name, all_symbols, limit=50)
            logger.info(f"📊 Scanning top {len(symbols)} {exchange_name.upper()} cryptos (by volume) out of {len(all_symbols)} total")

            # Scan each symbol on each timeframe - SKIP 15m, only scan 1h and 1d
            for idx, symbol in enumerate(symbols):
                try:
                    for timeframe_key in TIMEFRAMES.keys():
                        levels = await self.scan_symbol_timeframe(exchange_name, symbol, timeframe_key)
                        all_levels.extend(levels)

                        if levels:
                            logger.info(f"🎯 {symbol} ({timeframe_key}): {len(levels)} approaching liquidations")

                    # Rate limiting - reduced for faster scanning
                    await asyncio.sleep(0.05)

                except Exception as e:
                    logger.error(f"Error scanning {symbol} on {exchange_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning {exchange_name}: {e}")

        return all_levels

    async def scan_all_exchanges(self) -> List[LiquidationLevel]:
        """Scan all exchanges for approaching liquidations - Kraken, OKX, and Bybit"""
        logger.info("🚀 Starting liquidation scan...")
        all_levels = []

        # Scan all exchanges (Kraken, OKX, Bybit)
        exchange_order = list(self.exchanges.keys())

        # Scan each exchange
        for exchange_name in exchange_order:
            levels = await self.scan_exchange(exchange_name)
            all_levels.extend(levels)
            logger.info(f"✅ {exchange_name.upper()}: {len(levels)} approaching liquidations found")

        # Sort by distance (closest first)
        all_levels.sort(key=lambda x: x.distance_pct)

        logger.info(f"🎯 Total approaching liquidations found: {len(all_levels)}")
        return all_levels

    def create_discord_embeds(self, levels: List[LiquidationLevel]) -> List[Dict]:
        """Create Discord embeds by timeframe (15m/1h/1d) with colored cards"""
        if not levels:
            return [{
                "title": "🔍 Liquidation Scanner - No Signals",
                "description": "No coins approaching liquidation levels at this time.",
                "color": 0x808080,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]

        # Filter out stablecoin pairs, forex pairs, and gold pairs
        # ONLY show 80%+ importance (high-quality reversal zones with liquidity)
        filtered_levels = [
            l for l in levels
            if not self.is_stablecoin_pair(l.symbol)
            and not self.is_forex_or_gold_pair(l.symbol)
            and l.importance >= 90.0  # Only 90%+ importance (A+ setups only)
        ]

        if not filtered_levels:
            return [{
                "title": "🔍 Liquidation Scanner - No Signals",
                "description": "No A+ liquidation opportunities found (90%+ importance required).",
                "color": 0x808080,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }]

        # Group by timeframe
        levels_by_tf = {
            '15m': [l for l in filtered_levels if l.timeframe == '15m'],
            '1h': [l for l in filtered_levels if l.timeframe == '1h'],
            '1d': [l for l in filtered_levels if l.timeframe == '1d']
        }

        # Check if we should include daily liquidations (4-hour cooldown)
        include_daily = True
        if len(levels_by_tf['1d']) > 0:
            if self.last_daily_liquidation_sent is not None:
                time_since_last = (datetime.now(timezone.utc) - self.last_daily_liquidation_sent).total_seconds()
                hours_since_last = time_since_last / 3600
                if hours_since_last < 4:
                    include_daily = False
                    logger.info(f"⏰ Skipping daily liquidations (last sent {hours_since_last:.1f} hours ago, need 4 hours)")
            else:
                # First time sending daily, update timestamp
                self.last_daily_liquidation_sent = datetime.now(timezone.utc)

        MAX_DESC_LENGTH = 5500
        max_items_per_tf = 3

        def get_is_prediction(level):
            return getattr(level, 'is_prediction', False)

        def build_embed(tf_key: str, tf_name: str, color: int, levels_list: List[LiquidationLevel]) -> Optional[Dict]:
            if not levels_list:
                return None

            if tf_key == '1h':
                levels_list.sort(key=lambda x: (-x.importance, get_is_prediction(x), x.distance_pct), reverse=(True, True, False))
            elif tf_key == '1d':
                levels_list.sort(key=lambda x: (get_is_prediction(x), x.importance * (1 / max(x.distance_pct, 0.1))), reverse=True)
            else:  # 15m
                levels_list.sort(key=lambda x: (-x.importance, x.distance_pct))

            top_levels = levels_list[:max_items_per_tf]
            desc = f"**{tf_name} A+ Reversal Zones (90%+ Importance)**\n\n"
            for i, level in enumerate(top_levels, 1):
                direction = "🔴 SHORT" if level.type == "top" else "🟢 LONG"
                prediction_marker = "🔮 **FUTURE PREDICTION** " if get_is_prediction(level) else ""
                has_sfp = getattr(level, 'has_sfp', False)
                sfp_info = getattr(level, 'sfp_info', None)
                sfp_marker = " 🎯 **SFP+LIQ COMBO!**" if has_sfp else ""
                desc += f"{i}. {prediction_marker}[{level.symbol}]({level.tradingview_link}) - {direction} | ${level.level:.4f} | {level.distance_pct:.2f}% away | {level.importance:.0f}%{sfp_marker}\n"
                if has_sfp and sfp_info:
                    sfp_type = "🟢 BULLISH" if sfp_info.get('is_bullish', False) else "🔴 BEARISH"
                    desc += f"   └─ 🎯 SFP: {sfp_type} at ${sfp_info.get('mid', 0):.4f}\n"

            if len(desc) > MAX_DESC_LENGTH:
                desc = desc[:MAX_DESC_LENGTH - 3] + "..."

            total_sfp_combos = sum(1 for l in levels_list if getattr(l, 'has_sfp', False))
            return {
                "title": f"🔍 Liquidation Scanner - {tf_name}",
                "description": desc,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": f"{tf_name} | SFP Combos: {total_sfp_combos} | Total: {len(levels_list)}"
                }
            }

        embeds = []
        embed_15m = build_embed('15m', '15-Minute', 0xFFFFFF, levels_by_tf['15m'])
        embed_1h = build_embed('1h', '1-Hour', 0x00FF00, levels_by_tf['1h'])
        embed_1d = build_embed('1d', 'Daily', 0xFF0000, levels_by_tf['1d'] if include_daily else [])

        for embed in [embed_15m, embed_1h, embed_1d]:
            if embed:
                embeds.append(embed)

        return embeds

    async def send_discord_notification(self, levels: List[LiquidationLevel]) -> bool:
        """Send Discord notification with liquidation levels"""
        try:
            if not DISCORD_WEBHOOK:
                logger.error("❌ DISCORD_WEBHOOK not set. Skipping liquidation alerts.")
                return False
            embeds = self.create_discord_embeds(levels)

            # Log what we're sending
            logger.info(f"📤 Sending {len(embeds)} embed(s) to Discord")
            for i, embed in enumerate(embeds, 1):
                title = embed.get('title', 'Unknown')
                logger.info(f"  Embed {i}: {title}")

            # Discord allows max 10 embeds per message, split if needed
            MAX_EMBEDS_PER_MESSAGE = 10
            success = True

            for i in range(0, len(embeds), MAX_EMBEDS_PER_MESSAGE):
                batch = embeds[i:i + MAX_EMBEDS_PER_MESSAGE]
                payload = {
                    "embeds": batch
                }

                response = requests.post(
                    DISCORD_WEBHOOK,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )

                if response.status_code == 204:
                    logger.info(f"✅ Discord notification sent successfully (batch {i//MAX_EMBEDS_PER_MESSAGE + 1})")
                else:
                    logger.error(f"❌ Discord error: {response.status_code} - {response.text}")
                    success = False

                # Small delay between batches
                if i + MAX_EMBEDS_PER_MESSAGE < len(embeds):
                    await asyncio.sleep(1)

            return success

        except Exception as e:
            logger.error(f"❌ Error sending Discord notification: {e}")
            return False

    def is_stablecoin_pair(self, symbol: str) -> bool:
        """Check if symbol is a stablecoin pair - EXCLUDE ALL stablecoin pairs"""
        stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'PAXG']
        symbol_upper = symbol.upper()

        # Remove :USDT suffix for parsing (handles USDC/USDT:USDT format)
        clean_symbol = symbol_upper.replace(':USDT', '').strip()

        # Direct check for USDC/USDT in any format
        if 'USDC/USDT' in symbol_upper or 'USDT/USDC' in symbol_upper:
            return True

        # Split by / to get base and quote
        if '/' in clean_symbol:
            parts = clean_symbol.split('/')
            if len(parts) >= 2:
                base = parts[0].strip()
                quote = parts[1].strip()

                # If both base and quote are stablecoins, exclude it
                if base in stablecoins and quote in stablecoins:
                    return True

                # Exclude ANY stablecoin against USDT (USDC/USDT, DAI/USDT, etc.)
                if base in stablecoins and quote == 'USDT':
                    return True
                if quote in stablecoins and base == 'USDT':
                    return True

        return False

    def is_forex_or_gold_pair(self, symbol: str) -> bool:
        """Check if symbol is a forex or gold pair (we only trade crypto)"""
        # Forex pairs
        forex_pairs = ['EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'SGD', 'HKD',
                      'CNY', 'INR', 'KRW', 'MXN', 'BRL', 'ZAR', 'TRY', 'RUB', 'SEK',
                      'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON', 'BGN', 'HRK', 'ILS',
                      'PHP', 'THB', 'MYR', 'IDR', 'VND', 'PKR', 'BDT', 'LKR', 'KZT',
                      'UAH', 'EGP', 'NGN', 'KES', 'GHS', 'ETB', 'TZS', 'UGX', 'ZMW',
                      'XAG', 'XPD', 'XPT', 'XAU', 'XAUT', 'GOLD', 'SILVER', 'PLATINUM', 'PALLADIUM']

        symbol_upper = symbol.upper()
        clean_symbol = symbol_upper.replace(':USDT', '').strip()

        if '/' in clean_symbol:
            parts = clean_symbol.split('/')
            if len(parts) >= 1:
                base = parts[0].strip()
                # Check if base is a forex or gold symbol
                if base in forex_pairs:
                    return True
                # Also check for common patterns
                if any(fx in base for fx in ['EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF']):
                    return True
                if any(metal in base for metal in ['XAU', 'XAUT', 'GOLD', 'SILVER', 'XAG', 'XPD', 'XPT']):
                    return True
        return False

    async def send_best_trade_card(self, trades: List[LiquidationLevel]) -> bool:
        """Send orange card with all available PEAK REVERSAL trade opportunities"""
        try:
            if not DISCORD_WEBHOOK:
                logger.error("❌ DISCORD_WEBHOOK not set. Skipping trade card.")
                return False
            if not trades:
                return False

            # Put ALL available trades on one card (not limited to 2)
            # Calculate W/L stats
            wins = sum(1 for t in self.trades_history if t.status == 'WIN')
            losses = sum(1 for t in self.trades_history if t.status == 'LOSS')
            pending = sum(1 for t in self.trades_history if t.status == 'PENDING')
            total = wins + losses + pending
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

            # Start description with stats
            desc = f"**🏆 PEAK REVERSAL TRADE ALERTS**\n\n"
            desc += f"📊 **Track Record:** 🟢 {wins}W | 🔴 {losses}L | ⏳ {pending}P | 📈 {win_rate:.1f}% Win Rate\n\n"
            desc += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, level in enumerate(trades, 1):
                # Assign trade number and create trade record
                trade_number = self.trade_counter
                self.trade_counter += 1

                direction = "LONG" if level.type == "bottom" else "SHORT"
                direction_bias = "🟢 LONG REVERSAL" if level.type == "bottom" else "🔴 SHORT REVERSAL"

                # Get setup type from level (set in select_trade_opportunities)
                setup_type = getattr(level, 'setup_type', 'APPROACHING')
                is_swept = getattr(level, 'is_swept', False)
                is_approaching = getattr(level, 'is_approaching', False)

                # Detect trend for this trade
                trend = await self.detect_trend_direction(level.exchange, level.symbol, level.timeframe)
                trade_direction = "LONG" if level.type == "bottom" else "SHORT"
                is_trend_aligned = (
                    (trend == 'UP' and trade_direction == 'LONG') or
                    (trend == 'DOWN' and trade_direction == 'SHORT')
                )

                # Calculate trade details
                entry_price = level.current_price
                if direction == "LONG":
                    stop_loss = level.level * 0.99
                    take_profit = entry_price * 1.02
                else:
                    stop_loss = level.level * 1.01
                    take_profit = entry_price * 0.98

                risk_reward = abs(take_profit - entry_price) / abs(entry_price - stop_loss)

                # Create trade record for tracking
                trade_record = TradeRecord(
                    trade_number=trade_number,
                    symbol=level.symbol,
                    direction=direction,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    timestamp=datetime.now(timezone.utc),
                    status='PENDING'
                )
                self.trades_history.append(trade_record)

                # Build the trade description with better visual separation
                desc += f"**🔢 TRADE #{trade_number}: {level.symbol.upper()}** ({level.exchange.upper()})\n"
                desc += "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"

                # SETUP TYPE - most important info!
                desc += f"🎯 **Setup:** {setup_type}\n"

                # Direction
                desc += f"📊 **Direction:** {direction_bias}\n"

                # Distance indicator
                if is_approaching:
                    desc += f"📍 **Status:** APPROACHING - GET READY! ({level.distance_pct:.2f}% away)\n"
                elif is_swept:
                    desc += f"💧 **Status:** LIQUIDITY SWEPT - Entry zone active!\n"
                else:
                    desc += f"📏 **Distance:** {level.distance_pct:.2f}% from liquidation\n"

                # Trend status
                if is_trend_aligned:
                    desc += f"✅ **Trend:** {trend} (WITH trend)\n"
                else:
                    desc += f"⚠️ **Trend:** {trend} (REVERSAL play)\n"

                desc += f"💰 **Entry:** ${entry_price:.4f}\n"
                desc += f"🛑 **Stop Loss:** ${stop_loss:.4f}\n"
                desc += f"🎯 **Take Profit:** ${take_profit:.4f}\n"
                desc += f"⚖️ **Risk:Reward:** 1:{risk_reward:.2f}\n"
                desc += f"🔥 **Importance:** {level.importance:.0f}%\n"

                # Show SFP info if available
                has_sfp = getattr(level, 'has_sfp', False)
                sfp_info = getattr(level, 'sfp_info', None)
                if has_sfp and sfp_info:
                    sfp_type = "🟢 BULLISH" if sfp_info.get('is_bullish', False) else "🔴 BEARISH"
                    desc += f"🎯 **SFP:** {sfp_type} at ${sfp_info.get('mid', 0):.4f}\n"

                desc += f"🔗 [View Chart]({level.tradingview_link})\n\n"

                if i < len(trades):
                    desc += "═════════════════════════════════════\n\n"

            desc += f"⚠️ **Risk:** Use proper sizing. Entry at 0.5-1% away from level.\n"

            embed = {
                "title": f"🏆 {len(trades)} Peak Reversal Trades",
                "description": desc,
                "color": 0xFF8800,  # Orange color
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": f"Trade #{self.trade_counter - len(trades)}-{self.trade_counter - 1} | A+ Setups Only - SFP + Swept Liquidity = Ultimate Entry"
                }
            }

            payload = {"embeds": [embed]}
            response = requests.post(
                DISCORD_WEBHOOK,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 204:
                symbols = ", ".join([t.symbol for t in trades])
                logger.info(f"✅ Trade card sent: {symbols} (Trades #{self.trade_counter - len(trades)}-{self.trade_counter - 1})")
                return True
            else:
                logger.error(f"❌ Discord error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending trade card: {e}")
            return False

    async def detect_trend_direction(self, exchange_name: str, symbol: str, timeframe: str) -> str:
        """Detect trend direction using moving averages - returns 'UP', 'DOWN', or 'NEUTRAL'"""
        try:
            # Get OHLCV data for trend analysis
            df = await self.get_ohlcv(exchange_name, symbol, timeframe, 100)
            if df is None or len(df) < 50:
                return 'NEUTRAL'

            # Calculate EMAs for trend detection
            ema_fast = df['close'].ewm(span=20, adjust=False).mean()
            ema_slow = df['close'].ewm(span=50, adjust=False).mean()

            current_price = df['close'].iloc[-1]
            current_ema_fast = ema_fast.iloc[-1]
            current_ema_slow = ema_slow.iloc[-1]

            # Trend is UP if: price > fast EMA > slow EMA
            # Trend is DOWN if: price < fast EMA < slow EMA
            if current_price > current_ema_fast > current_ema_slow:
                return 'UP'
            elif current_price < current_ema_fast < current_ema_slow:
                return 'DOWN'
            else:
                return 'NEUTRAL'
        except Exception as e:
            logger.debug(f"Error detecting trend for {symbol}: {e}")
            return 'NEUTRAL'

    async def select_trade_opportunities(self, levels: List[LiquidationLevel]) -> List[LiquidationLevel]:
        """Select top 2 coins with PEAK REVERSAL potential - SFP + SWEPT LIQUIDITY at 0.5%-1% away"""
        if not levels:
            return []

        # PRIORITIZE 1h timeframes - A+ setups only (90%+ importance)
        short_term_levels = [
            l for l in levels
            if l.timeframe == '1h'  # Only 1h
            and l.importance >= 90.0  # Only 90%+ importance (A+ setups only)
        ]

        # Filter out stablecoin pairs, forex pairs, and gold pairs
        filtered_levels = []
        for l in short_term_levels:
            if self.is_stablecoin_pair(l.symbol):
                continue
            elif self.is_forex_or_gold_pair(l.symbol):
                continue
            else:
                filtered_levels.append(l)

        short_term_levels = filtered_levels

        if not short_term_levels:
            logger.info("No 1h liquidation opportunities found (90%+ A+ setups required)")
            return []

        # Score each level for PEAK REVERSAL potential
        scored_levels = []
        for level in short_term_levels:
            # Get recent price data
            df = await self.get_ohlcv(level.exchange, level.symbol, '1h', 50)
            if df is None or len(df) < 36:
                continue

            # Detect sweeps
            sweeps = self.detect_sweeps(df)

            # Check SFP
            has_sfp = getattr(level, 'has_sfp', False)
            sfp_info = getattr(level, 'sfp_info', None)

            # Enhanced liquidity and volume analysis (for trade selection scoring)
            liq_data = self.calculate_enhanced_liquidity(df, lookback=20)
            vwap_data = self.calculate_vwap_analysis(df, multiplier=1.5)
            absorption_data = self.detect_volume_absorption(df, rvol_len=20, rvol_min=1.5)
            abnormal_vol_data = self.detect_abnormal_volume(df, lookback=20, vol_multiplier=2.0, extreme_multiplier=3.5)
            liq_divergence = self.calculate_liquidity_divergence(df, lookback=10)

            # Check sweep status
            is_fully_swept = False
            is_potential_sweep = False
            is_approaching = False  # 0.5% - 1% away

            # APPROACHING ZONE (0.5% - 1% away) - GET READY!
            if 0.5 <= level.distance_pct <= 1.0:
                is_approaching = True
                logger.info(f"🎯 APPROACHING ZONE: {level.symbol} - {level.distance_pct:.2f}% away from {level.type.upper()} liquidation")

            # Check if sweep happened (liquidity taken)
            if level.type == 'bottom':
                if sweeps['sweep_low_happened']:
                    is_fully_swept = True
                if sweeps['potential_sweep_low']:
                    is_potential_sweep = True
                # Direct price check for sweep
                recent_candles = df.tail(3)
                if recent_candles['low'].min() <= level.level * 1.002:
                    # Price wicked below level (swept)
                    if level.current_price > level.level:
                        is_fully_swept = True  # Swept and reversing
            else:  # top
                if sweeps['sweep_high_happened']:
                    is_fully_swept = True
                if sweeps['potential_sweep_high']:
                    is_potential_sweep = True
                # Direct price check for sweep
                recent_candles = df.tail(3)
                if recent_candles['high'].max() >= level.level * 0.998:
                    # Price wicked above level (swept)
                    if level.current_price < level.level:
                        is_fully_swept = True  # Swept and reversing

            # Detect trend direction
            trend = await self.detect_trend_direction(level.exchange, level.symbol, level.timeframe)
            trade_direction = "LONG" if level.type == "bottom" else "SHORT"

            # Check trend alignment
            is_trend_aligned = (
                (trend == 'UP' and trade_direction == 'LONG') or
                (trend == 'DOWN' and trade_direction == 'SHORT')
            )

            # Quality reversal = counter-trend but high importance
            is_quality_reversal = level.importance >= 90

            score = 0.0
            setup_type = []

            # ===== PEAK REVERSAL SCORING =====

            # 1. SFP + SWEPT LIQUIDITY = ULTIMATE ENTRY (HIGHEST PRIORITY)
            if has_sfp and is_fully_swept:
                score += 500  # ULTIMATE combo - SFP + swept liquidity
                setup_type.append("🎯 SFP+SWEPT")
                logger.info(f"🎯🎯🎯 ULTIMATE ENTRY: {level.symbol} - SFP + SWEPT LIQUIDITY at ${level.level:.4f}")

            # 2. SFP only (still very good)
            elif has_sfp:
                score += 300
                setup_type.append("🎯 SFP")
                logger.info(f"🎯🎯 SFP ENTRY: {level.symbol} - SFP at ${level.level:.4f}")

            # 3. Swept liquidity only (good reversal)
            elif is_fully_swept:
                score += 250
                setup_type.append("💧 SWEPT")
                logger.info(f"💧 SWEPT LIQUIDITY: {level.symbol} - Liquidity swept at ${level.level:.4f}")

            # 4. APPROACHING ZONE (0.5% - 1% away) - GET READY FOR POTENTIAL TRADE
            if is_approaching:
                score += 150  # Bonus for approaching ideal entry zone
                setup_type.append("📍 APPROACHING")
                logger.info(f"📍 APPROACHING ZONE: {level.symbol} at {level.distance_pct:.2f}% - GET READY!")

            # 5. Potential sweep (price approaching liquidity)
            if is_potential_sweep:
                score += 100
                setup_type.append("⚡ POTENTIAL SWEEP")
                logger.info(f"⚡ POTENTIAL SWEEP: {level.symbol} - {level.type.upper()} at ${level.level:.4f}")

            # 6. Trend alignment bonus
            if is_trend_aligned:
                score += 50
            elif is_quality_reversal:
                score += 30  # Quality counter-trend reversal

            # 7. Distance scoring - prioritize 0.5% - 1% away (get ready zone)
            if 0.5 <= level.distance_pct <= 1.0:
                score += 80  # PERFECT distance - get ready!
            elif 0.3 <= level.distance_pct < 0.5:
                score += 60  # Very close - almost there
            elif 1.0 < level.distance_pct <= 1.5:
                score += 50  # Good distance
            elif 1.5 < level.distance_pct <= 2.0:
                score += 30  # Decent
            elif level.distance_pct < 0.3:
                score += 40  # Already at level - might be swept
            else:
                score += 10  # Too far

            # 8. Importance multiplier
            score += level.importance * 0.5

            # 9. Enhanced liquidity spike boost (from Liquidity Hunter Scalp Pro)
            if liq_data['is_liquidity_spike']:
                score += 40  # Strong liquidity spike = high quality setup
                if liq_data['z_score'] >= 2.0:
                    score += 20  # Very strong Z-score

            # 10. VWAP extreme boost (price far from VWAP = strong reversal potential)
            if vwap_data['is_vwap_extreme']:
                score += 30

            # 11. Volume absorption boost (high volume, small range = smart money absorption)
            if absorption_data['is_absorption']:
                score += 35  # Absorption = strong reversal signal

            # 12. Abnormal/extreme volume boost (from VPSR Pro)
            if abnormal_vol_data['is_extreme_volume']:
                score += 50  # Extreme volume = major event
            elif abnormal_vol_data['is_abnormal_volume']:
                score += 25  # Abnormal volume = significant

            # 13. Reversal signal boost (extreme volume followed by reversal candle)
            if level.type == 'bottom' and abnormal_vol_data['bullish_reversal']:
                score += 45  # Bullish reversal after extreme volume = strong setup
            elif level.type == 'top' and abnormal_vol_data['bearish_reversal']:
                score += 45  # Bearish reversal after extreme volume = strong setup

            # 14. Liquidity divergence boost (price vs liquidity divergence)
            if level.type == 'bottom' and liq_divergence['bullish_divergence']:
                score += 35  # Bullish liquidity divergence
            elif level.type == 'top' and liq_divergence['bearish_divergence']:
                score += 35  # Bearish liquidity divergence

            # Skip low scores
            if score < 100:
                continue

            setup_str = " + ".join(setup_type) if setup_type else "APPROACHING"

            # Store setup_str on the level for trade card display
            level.setup_type = setup_str
            level.is_swept = is_fully_swept
            level.is_approaching = is_approaching

            scored_levels.append((score, level, trend, is_trend_aligned, is_fully_swept, has_sfp, is_approaching, setup_str))

        # Sort by score descending (highest score first)
        scored_levels.sort(key=lambda x: x[0], reverse=True)

        # Log top candidates
        if scored_levels:
            logger.info(f"📊 Top trade candidates (sorted by score):")
            for i, (score, level, trend, aligned, swept, sfp, approaching, setup) in enumerate(scored_levels[:5]):
                logger.info(f"   {i+1}. {level.symbol} - Score: {score:.0f} | Setup: {setup} | {level.distance_pct:.2f}% away")

        # Get EXACTLY 2 unique symbols (avoid duplicates)
        selected = []
        seen_symbols = set()
        for score, level, trend, aligned, swept, sfp, approaching, setup in scored_levels:
            if level.symbol not in seen_symbols and len(selected) < 2:
                selected.append(level)
                seen_symbols.add(level.symbol)

                # Log selection
                sfp_status = "🎯 SFP" if sfp else ""
                sweep_status = "💧 SWEPT" if swept else ""
                approach_status = "📍 0.5-1% AWAY" if approaching else ""
                trend_status = "✅ WITH TREND" if aligned else "⚠️ REVERSAL"

                logger.info(f"✅ SELECTED #{len(selected)}: {level.symbol} ({level.timeframe})")
                logger.info(f"   Score: {score:.0f} | Distance: {level.distance_pct:.2f}%")
                logger.info(f"   Setup: {setup} | Trend: {trend} {trend_status}")

        if len(selected) < 2:
            logger.info(f"⚠️ Only found {len(selected)} A+ trade opportunity(ies) (looking for 2)")

        return selected

    async def execute_trade(self, level: LiquidationLevel) -> bool:
        """Execute trade based on liquidation level"""
        try:
            exchange = self.exchanges.get(level.exchange)
            if not exchange:
                logger.error(f"Exchange {level.exchange} not available")
                return False

            # Determine trade direction based on liquidation type
            # BOTTOM liquidation = shorts liquidated = LONG reversal (buy)
            # TOP liquidation = longs liquidated = SHORT reversal (sell)
            direction = "long" if level.type == "bottom" else "short"
            side = "buy" if direction == "long" else "sell"

            # Calculate position size (1% of account, fallback to $50)
            position_size = 50.0
            try:
                balance = await asyncio.get_event_loop().run_in_executor(
                    None, exchange.fetch_balance
                )
                usdt_balance = balance.get('USDT', {}).get('free') or balance.get('USDT', {}).get('total')
                if usdt_balance:
                    position_size = max(10.0, usdt_balance * 0.01)  # 1% risk, min $10
            except Exception:
                pass

            # Calculate stop loss and take profit
            # Stop loss: 1% beyond liquidation level
            # Take profit: 2% from entry (2:1 R:R)
            if direction == "long":
                entry_price = level.current_price
                stop_loss = level.level * 0.99  # 1% below liquidation level
                take_profit = entry_price * 1.02  # 2% above entry
            else:
                entry_price = level.current_price
                stop_loss = level.level * 1.01  # 1% above liquidation level
                take_profit = entry_price * 0.98  # 2% below entry

            # Calculate quantity
            quantity = position_size / entry_price

            logger.info(f"📈 Executing {direction.upper()} trade: {level.symbol} @ ${entry_price:.4f}")
            logger.info(f"   Stop Loss: ${stop_loss:.4f} | Take Profit: ${take_profit:.4f}")

            # Place market order
            try:
                params = {}
                if level.exchange == 'okx':
                    params = {
                        'tdMode': 'cross',
                        'posSide': 'long' if direction == 'long' else 'short',
                        'reduceOnly': False,
                        'tpTriggerPx': take_profit,
                        'tpOrdPx': '-1',
                        'slTriggerPx': stop_loss,
                        'slOrdPx': '-1',
                    }
                # Futures/swap order
                order = await asyncio.get_event_loop().run_in_executor(
                    None,
                    exchange.create_order,
                    level.symbol,
                    'market',
                    side,
                    quantity,
                    None,
                    params
                )

                if order:
                    logger.info(f"✅ Trade executed: {order.get('id', 'N/A')}")
                    return True
                else:
                    logger.error("❌ Order failed - no order ID returned")
                    return False

            except Exception as e:
                logger.error(f"❌ Error placing order: {e}")
                # Try simpler order without stop loss/take profit
                try:
                    order = await asyncio.get_event_loop().run_in_executor(
                        None,
                        exchange.create_order,
                        level.symbol,
                        'market',
                        side,
                        quantity
                    )
                    if order:
                        logger.info(f"✅ Trade executed (simple): {order.get('id', 'N/A')}")
                        return True
                except Exception as e2:
                    logger.error(f"❌ Simple order also failed: {e2}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error executing trade for {level.symbol}: {e}")
            return False

    async def run_scan(self) -> List[LiquidationLevel]:
        """Run complete liquidation scan"""
        logger.info("🎯 Starting liquidation scan...")
        start_time = time.time()

        # Scan all exchanges
        levels = await self.scan_all_exchanges()

        # Select EXACTLY 2 trade opportunities (15m and 1h only, no stablecoins, trend-aligned)
        trade_opportunities = await self.select_trade_opportunities(levels)

        # Ensure we only have max 2 trades
        if len(trade_opportunities) > 2:
            trade_opportunities = trade_opportunities[:2]
            logger.warning(f"⚠️ Limited to 2 trades (had {len(trade_opportunities)} opportunities)")

        # Get best 2 trades for orange card (highest potential moves - A+ setups only)
        best_trades = trade_opportunities[:2] if trade_opportunities else []
        executed_trades = []
        for opportunity in trade_opportunities:
            logger.info(f"📈 Attempting to execute trade: {opportunity.symbol} ({opportunity.timeframe}) - {opportunity.type.upper()} liquidation")
            success = await self.execute_trade(opportunity)
            if success:
                executed_trades.append(opportunity)
                logger.info(f"✅ Trade executed successfully: {opportunity.symbol}")
            else:
                logger.warning(f"❌ Trade execution failed: {opportunity.symbol}")
            # Small delay between trades
            await asyncio.sleep(2)

        # Log final count
        logger.info(f"📊 Trade execution summary: {len(executed_trades)}/{len(trade_opportunities)} trades executed")

        # Send best trade orange card with 2 trades
        if best_trades:
            try:
                await self.send_best_trade_card(best_trades)
            except AttributeError:
                # Fallback if method doesn't exist
                logger.warning("⚠️ send_best_trade_card method not found, skipping")
            except Exception as e:
                logger.error(f"❌ Error sending best trade card: {e}")

        # Send Discord notification for all liquidations
        await self.send_discord_notification(levels)

        scan_time = time.time() - start_time
        logger.info(f"✅ Scan completed in {scan_time:.2f} seconds")
        logger.info(f"📈 Executed {len(executed_trades)} trades")

        return levels

# Paper trading removed - focusing on A+ setups only

async def main():
    """Main scanner function"""
    scanner = LiquidationScanner()

    try:
        # Calculate next :45 time (every 2 hours: 00:45, 02:45, 04:45, etc.)
        def get_next_scan_time():
            now = datetime.now(timezone.utc)
            current_hour = now.hour
            current_minute = now.minute

            # Find next even hour :45 (0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22)
            # Round current hour down to nearest even hour
            base_hour = (current_hour // 2) * 2

            # If we're past :45 in current hour, move to next 2-hour cycle
            if current_minute >= 45:
                base_hour = (base_hour + 2) % 24

            next_time = now.replace(hour=base_hour, minute=45, second=0, microsecond=0)

            # If the calculated time is in the past, add 2 hours
            if next_time <= now:
                next_time += timedelta(hours=2)

            return next_time

        # Wait until next :45 time
        next_scan = get_next_scan_time()
        wait_seconds = (next_scan - datetime.now(timezone.utc)).total_seconds()
        if wait_seconds > 0:
            logger.info(f"⏰ Waiting until {next_scan.strftime('%H:%M:%S')} UTC for first scan ({wait_seconds/60:.1f} minutes)...")
            await asyncio.sleep(wait_seconds)

        # Run continuous scans every 2 hours at :45
        while True:
            levels = await scanner.run_scan()

            # Wait 2 hours (7200 seconds) for next scan
            logger.info("⏰ Waiting 2 hours for next scan at :45...")
            await asyncio.sleep(7200)  # 2 hours

    except KeyboardInterrupt:
        logger.info("🛑 Scanner stopped by user")
    except Exception as e:
        logger.error(f"❌ Scanner error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
