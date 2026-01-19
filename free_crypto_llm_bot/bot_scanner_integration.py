#!/usr/bin/env python3
"""
Bot Scanner Integration - Allows querying existing bots for specific conditions
"""
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional
import logging
import pandas as pd
import numpy as np
import ccxt
import asyncio

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent

# Common symbols to scan
TOP_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT",
    "XRP/USDT", "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT",
    "MATIC/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "ALGO/USDT"
]

class LiquidationScannerIntegration:
    """Integration with Liquidation Scanner Bot"""

    def __init__(self):
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        """Initialize exchange connection"""
        try:
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}
            })
        except Exception as e:
            logger.warning(f"Could not init exchange: {e}")

    def scan_for_liquidation_stacks(self, timeframe: str = "15m", max_distance_pct: float = 5.0) -> List[Dict]:
        """
        Scan for coins close to liquidation stacks

        Args:
            timeframe: Timeframe to check (15m, 1h, 1d)
            max_distance_pct: Maximum distance from liquidation level (default: 5%)

        Returns:
            List of coins with liquidation levels nearby
        """
        if not self.exchange:
            return []

        results = []

        for symbol in TOP_SYMBOLS[:10]:  # Scan top 10 for speed
            try:
                # Fetch OHLCV data
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=200)
                if not ohlcv or len(ohlcv) < 50:
                    continue

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

                # Detect liquidation levels (simplified version)
                liquidation = self._detect_liquidation_level(df, timeframe)
                if not liquidation:
                    continue

                current_price = df['close'].iloc[-1]
                liq_level = liquidation['level']
                distance_pct = abs(current_price - liq_level) / current_price * 100

                if distance_pct <= max_distance_pct:
                    results.append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'liquidation_level': liq_level,
                        'current_price': current_price,
                        'distance_pct': distance_pct,
                        'importance': liquidation.get('importance', 0),
                        'type': liquidation.get('type', 'unknown')
                    })
            except Exception as e:
                logger.warning(f"Error scanning {symbol}: {e}")
                continue

        # Sort by distance (closest first)
        results.sort(key=lambda x: x['distance_pct'])
        return results

    def _detect_liquidation_level(self, df: pd.DataFrame, timeframe: str) -> Optional[Dict]:
        """Detect liquidation level from price action"""
        if len(df) < 50:
            return None

        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values

        # Volume analysis
        volume_lookback = 50
        avg_volume = np.mean(volume[-volume_lookback:])
        volume_std = np.std(volume[-volume_lookback:])

        # Check recent candles
        for i in range(max(volume_lookback, len(df) - 10), len(df)):
            candle_volume = volume[i]
            volume_z = (candle_volume - avg_volume) / volume_std if volume_std > 0 else 0

            if volume_z < 2.0:  # Need abnormal volume
                continue

            # Liquidation size
            range_pu = high[i] - low[i]
            volume_m = candle_volume / 1e6
            liquidation_size = volume_m * range_pu

            if liquidation_size < 5.0:
                continue

            # Determine liquidation level
            is_bearish = close[i] < open_price[i]
            if is_bearish:
                liq_level = high[i]  # Long liquidation at high
                liq_type = "top"
            else:
                liq_level = low[i]  # Short liquidation at low
                liq_type = "bottom"

            # Calculate importance
            importance = 0.0
            if volume_z >= 3.0:
                importance += 40.0
            elif volume_z >= 2.0:
                importance += 25.0

            if liquidation_size >= 5.0:
                importance += 30.0

            return {
                'level': liq_level,
                'type': liq_type,
                'importance': importance
            }

        return None


class ShortSniperIntegration:
    """Integration with Short Sniper Bot"""

    def __init__(self):
        self.exchange = None
        self._init_exchange()

    def _init_exchange(self):
        """Initialize exchange connection"""
        try:
            self.exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}
            })
        except Exception as e:
            logger.warning(f"Could not init exchange: {e}")

    def scan_for_deviation_vwap(self, deviation_level: int = 2, direction: str = "above") -> List[Dict]:
        """
        Scan for coins at deviation VWAP zones

        Args:
            deviation_level: Deviation level to find (2 for 2a+, 3 for 3a+)
            direction: "above" for shorts (2a+/3a+ above VWAP), "below" for longs

        Returns:
            List of coins at specified deviation zone
        """
        if not self.exchange:
            return []

        results = []

        for symbol in TOP_SYMBOLS[:15]:  # Scan top 15
            try:
                # Fetch daily data for VWAP calculation
                ohlcv = self.exchange.fetch_ohlcv(symbol, '1d', limit=100)
                if not ohlcv or len(ohlcv) < 50:
                    continue

                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)

                # Calculate VWAP with deviation bands
                vwap_data = self._calculate_vwap_bands(df)
                if not vwap_data:
                    continue

                current_price = df['close'].iloc[-1]
                vwap = vwap_data['vwap']
                std_dev = vwap_data['std_dev']

                # Calculate deviation
                deviation = (current_price - vwap) / std_dev if std_dev > 0 else 0

                # Check if matches criteria
                if direction == "above":
                    # Looking for shorts (price above VWAP)
                    if deviation >= deviation_level:
                        distance_from_band = current_price - vwap_data[f'upper{deviation_level}']
                        results.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'vwap': vwap,
                            'deviation_level': deviation_level,
                            'deviation_sigma': deviation,
                            'distance_from_band': distance_from_band,
                            'upper2': vwap_data.get('upper2', 0),
                            'upper3': vwap_data.get('upper3', 0),
                            'zone': f"{deviation_level}a+"
                        })
                else:
                    # Looking for longs (price below VWAP)
                    if deviation <= -deviation_level:
                        distance_from_band = vwap_data[f'lower{deviation_level}'] - current_price
                        results.append({
                            'symbol': symbol,
                            'current_price': current_price,
                            'vwap': vwap,
                            'deviation_level': deviation_level,
                            'deviation_sigma': abs(deviation),
                            'distance_from_band': distance_from_band,
                            'lower2': vwap_data.get('lower2', 0),
                            'lower3': vwap_data.get('lower3', 0),
                            'zone': f"{deviation_level}a+"
                        })
            except Exception as e:
                logger.warning(f"Error scanning {symbol}: {e}")
                continue

        # Sort by deviation (highest first for shorts, lowest first for longs)
        if direction == "above":
            results.sort(key=lambda x: x['deviation_sigma'], reverse=True)
        else:
            results.sort(key=lambda x: x['deviation_sigma'])

        return results

    def _calculate_vwap_bands(self, df: pd.DataFrame) -> Optional[Dict]:
        """Calculate VWAP with deviation bands"""
        if len(df) < 20:
            return None

        # Calculate VWAP (volume-weighted average price)
        df = df.copy()
        df['hlc3'] = (df['high'] + df['low'] + df['close']) / 3
        df['pv'] = df['hlc3'] * df['volume']

        # Reset on new day
        df['date'] = df.index.date
        df['date_change'] = df['date'] != df['date'].shift(1)

        # Calculate VWAP per day
        vwap_values = []
        std_values = []

        current_sum_pv = 0
        current_sum_v = 0
        current_sum_pv2 = 0

        for idx, row in df.iterrows():
            if row['date_change']:
                current_sum_pv = row['pv']
                current_sum_v = row['volume']
                current_sum_pv2 = (row['hlc3'] ** 2) * row['volume']
            else:
                current_sum_pv += row['pv']
                current_sum_v += row['volume']
                current_sum_pv2 += (row['hlc3'] ** 2) * row['volume']

            if current_sum_v > 0:
                vwap = current_sum_pv / current_sum_v
                variance = (current_sum_pv2 / current_sum_v) - (vwap ** 2)
                std_dev = np.sqrt(max(variance, 0))

                vwap_values.append(vwap)
                std_values.append(std_dev)
            else:
                vwap_values.append(np.nan)
                std_values.append(np.nan)

        df['vwap'] = vwap_values
        df['std_dev'] = std_values

        latest_vwap = df['vwap'].iloc[-1]
        latest_std = df['std_dev'].iloc[-1]

        if pd.isna(latest_vwap) or pd.isna(latest_std) or latest_std == 0:
            return None

        current_price = df['close'].iloc[-1]

        # Calculate bands
        upper1 = latest_vwap + (latest_std * 1.0)
        lower1 = latest_vwap - (latest_std * 1.0)
        upper2 = latest_vwap + (latest_std * 2.0)  # 2a+ zone
        lower2 = latest_vwap - (latest_std * 2.0)
        upper3 = latest_vwap + (latest_std * 3.0)  # 3a+ zone
        lower3 = latest_vwap - (latest_std * 3.0)

        return {
            'vwap': latest_vwap,
            'std_dev': latest_std,
            'upper1': upper1,
            'lower1': lower1,
            'upper2': upper2,
            'lower2': lower2,
            'upper3': upper3,
            'lower3': lower3,
            'current_price': current_price
        }



