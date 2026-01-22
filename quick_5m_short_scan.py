#!/usr/bin/env python3
"""
Quick 5-Minute Short Scanner
Scans for coins approaching TOP liquidation levels on 5m timeframe (short opportunities)
"""

import asyncio
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Optional, Dict
import ccxt

# Configuration
DISCORD_WEBHOOK = ""

# Liquidation detection parameters
LIQUIDATION_PARAMS = {
    'volume_multiplier': 2.5,
    'volume_lookback': 50,
    'min_liquidation_size': 3.0,  # Lower for 5m
    'z_score_threshold': 2.0,
    'min_importance_for_signal': 35.0,  # Lower for 5m
    'max_distance_pct': 2.5  # Alert if within 2.5% of liquidation level
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exchange configuration
EXCHANGES = {
    'mexc': {
        'class': ccxt.mexc,
        'sandbox': False,
        'rateLimit': 1000,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    }
}

class Quick5mShortScanner:
    """Quick scanner for 5m short opportunities at top liquidations"""

    def __init__(self):
        self.exchanges = {}
        for name, config in EXCHANGES.items():
            self.exchanges[name] = config['class'](config)

    def is_stablecoin_pair(self, symbol: str) -> bool:
        """Check if symbol is a stablecoin-to-stablecoin pair"""
        stablecoins = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDD', 'USDP', 'FDUSD', 'US', 'STBL']
        parts = symbol.replace(':', '/').split('/')
        if len(parts) >= 2:
            base = parts[0].upper()
            quote = parts[1].upper()
            # Check if both base and quote are stablecoins
            if base in stablecoins and quote in stablecoins:
                return True
            # Also check if it's a stablecoin/USDT pair (we don't trade these)
            if base in stablecoins and quote == 'USDT':
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

        parts = symbol.replace(':', '/').split('/')
        if len(parts) >= 1:
            base = parts[0].upper()
            # Check if base is a forex or gold symbol
            if base in forex_pairs:
                return True
            # Also check for common patterns
            if any(fx in base for fx in ['EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF']):
                return True
            if any(metal in base for metal in ['XAU', 'XAUT', 'GOLD', 'SILVER', 'XAG', 'XPD', 'XPT']):
                return True
        return False

    def detect_liquidation_levels(self, df: pd.DataFrame) -> List[Dict]:
        """Detect liquidation levels from OHLCV data"""
        if len(df) < 50:
            return []

        liquidations = []
        volume_lookback = LIQUIDATION_PARAMS['volume_lookback']

        # Calculate ATR for volatility
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values
        volume = df['volume'].values

        # ATR calculation
        tr_list = []
        for i in range(1, len(df)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            tr_list.append(tr)
        atr14 = np.mean(tr_list[-14:]) if len(tr_list) >= 14 else (high[-1] - low[-1])

        # Volume statistics
        volume_array = volume[-volume_lookback:]
        avg_volume = np.mean(volume_array)
        volume_std = np.std(volume_array) if len(volume_array) > 1 else 1

        # Scan recent candles for liquidations
        for i in range(max(volume_lookback, len(df) - 20), len(df)):
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

                # Major liquidation detection
                is_major_liquidation = (liquidation_size >= LIQUIDATION_PARAMS['min_liquidation_size']) or \
                                       (abnormal_volume and liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold'] * 0.8) or \
                                       very_abnormal_volume

                if not is_major_liquidation:
                    continue

                # Calculate importance score (0-100)
                importance = 0.0

                # Volume component
                if very_abnormal_volume:
                    importance += 40.0
                elif abnormal_volume:
                    importance += 25.0
                elif candle_volume > avg_volume * LIQUIDATION_PARAMS['volume_multiplier']:
                    importance += 10.0

                # Liquidation size component
                if liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold'] * 1.5:
                    importance += 30.0
                elif liquidation_z >= LIQUIDATION_PARAMS['z_score_threshold']:
                    importance += 20.0
                elif liquidation_size >= LIQUIDATION_PARAMS['min_liquidation_size']:
                    importance += 10.0

                # Price range component
                if atr14 > 0:
                    range_ratio = range_pu / atr14
                    if range_ratio > 3.0:
                        importance += 20.0
                    elif range_ratio > 2.0:
                        importance += 15.0
                    elif range_ratio > 1.5:
                        importance += 10.0

                # Wick rejection component
                if range_pu > 0:
                    wick_size = (candle_high - max(candle_close, candle_open)) + (min(candle_close, candle_open) - candle_low)
                    wick_ratio = wick_size / range_pu
                    if wick_ratio > 0.6:
                        importance += 10.0
                    elif wick_ratio > 0.4:
                        importance += 5.0

                importance = min(100.0, importance)

                # Only track significant liquidations
                if importance < LIQUIDATION_PARAMS['min_importance_for_signal']:
                    continue

                # Determine liquidation level and type
                is_bearish_candle = candle_close < candle_open
                if is_bearish_candle:
                    # Bearish liquidation - likely cleared longs (wick above) = TOP liquidation
                    liq_level = candle_high
                    liq_type = "top"  # Longs got liquidated at top = SHORT opportunity
                else:
                    # Skip bottom liquidations for short scanner
                    continue

                liquidations.append({
                    "level": liq_level,
                    "importance": importance,
                    "type": liq_type,
                    "liquidation_size": liquidation_size,
                    "volume_z": volume_z,
                    "liquidation_z": liquidation_z,
                    "candle_index": i
                })

            except Exception as e:
                continue

        # Sort by importance (highest first)
        liquidations.sort(key=lambda x: x["importance"], reverse=True)
        return liquidations

    async def get_symbols(self, exchange_name: str) -> List[str]:
        """Get top volume symbols from MEXC"""
        try:
            exchange = self.exchanges[exchange_name]
            markets = await asyncio.get_event_loop().run_in_executor(
                None, exchange.load_markets
            )

            symbols = []
            for symbol, market in markets.items():
                if (market.get('quote') == 'USDT' and
                    market.get('active', True) and
                    (market.get('swap', False) or market.get('type') in ['swap', 'future']) and
                    'USDT' in symbol):
                    symbols.append(symbol)

            # Get top volume symbols
            tickers = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_tickers
            )

            symbol_volumes = []
            for symbol in symbols:
                ticker = tickers.get(symbol, {})
                volume = ticker.get('quoteVolume', 0) or ticker.get('baseVolume', 0) or 0
                if volume > 0:
                    symbol_volumes.append((symbol, volume))

            symbol_volumes.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in symbol_volumes[:150]]  # Top 150 by volume

        except Exception as e:
            logger.error(f"Error getting symbols from {exchange_name}: {e}")
            return []

    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '5m', limit: int = 100) -> Optional[pd.DataFrame]:
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
            logger.debug(f"Error getting OHLCV for {symbol}: {e}")
            return None

    def get_tradingview_link(self, symbol: str) -> str:
        """Generate TradingView link for symbol"""
        base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        tv_symbol = f"{base_symbol}USDT.P"
        return f"https://www.tradingview.com/chart/?symbol=MEXC:{tv_symbol}"

    async def scan_symbol(self, symbol: str) -> List[Dict]:
        """Scan single symbol for 5m top liquidations"""
        results = []

        try:
            df = await self.get_ohlcv('mexc', symbol, '5m', 100)
            if df is None or len(df) < 50:
                return results

            current_price = df['close'].iloc[-1]
            liquidations = self.detect_liquidation_levels(df)

            # Check distance to liquidation levels (only TOP liquidations)
            for liq in liquidations:
                if liq['type'] != 'top':
                    continue

                liq_level = liq['level']
                distance_pct = abs(current_price - liq_level) / current_price * 100 if current_price > 0 else 999

                # Only alert if within max distance and price is below liquidation level (approaching from below)
                if distance_pct <= LIQUIDATION_PARAMS['max_distance_pct'] and current_price < liq_level:
                    tradingview_link = self.get_tradingview_link(symbol)

                    results.append({
                        'symbol': symbol,
                        'exchange': 'mexc',
                        'timeframe': '5m',
                        'level': liq_level,
                        'type': liq['type'],
                        'importance': liq['importance'],
                        'current_price': current_price,
                        'distance_pct': distance_pct,
                        'liquidation_size': liq['liquidation_size'],
                        'tradingview_link': tradingview_link
                    })

        except Exception as e:
            logger.debug(f"Error scanning {symbol}: {e}")

        return results

    async def run_scan(self) -> List[Dict]:
        """Run complete 5m short scan"""
        logger.info("🔍 Starting 5-minute SHORT scan...")
        start_time = asyncio.get_event_loop().time()

        # Get symbols
        symbols = await self.get_symbols('mexc')
        logger.info(f"📊 Scanning {len(symbols)} symbols on MEXC (5m timeframe)")

        # Scan symbols concurrently (with rate limiting)
        all_results = []
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

        async def scan_with_limit(symbol):
            async with semaphore:
                results = await self.scan_symbol(symbol)
                if results:
                    logger.info(f"🎯 {symbol}: Found {len(results)} top liquidation(s) for SHORT")
                return results

        tasks = [scan_with_limit(symbol) for symbol in symbols]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        for result in results_list:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Task error: {result}")

        # Filter out stablecoin pairs, forex pairs, and gold pairs
        all_results = [
            r for r in all_results
            if not self.is_stablecoin_pair(r['symbol'])
            and not self.is_forex_or_gold_pair(r['symbol'])
        ]

        # Sort by distance (closest first) and importance
        all_results.sort(key=lambda x: (x['distance_pct'], -x['importance']))

        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ Scan completed in {elapsed:.1f} seconds. Found {len(all_results)} short opportunities")

        return all_results

    def send_discord_results(self, results: List[Dict]):
        """Send results to Discord"""
        if not results:
            logger.info("No results to send")
            return

        # Take top 10 results
        top_results = results[:10]

        embeds = []

        # Main embed
        desc = f"**🔴 5-Minute SHORT Opportunities**\n\n"
        desc += f"Found **{len(results)}** coins approaching TOP liquidation levels (longs liquidated = short opportunity)\n\n"
        desc += "💡 **Setup:** Price approaching liquidation level where longs were liquidated. Watch for rejection/cascade.\n\n"

        for i, result in enumerate(top_results, 1):
            symbol = result['symbol']
            level = result['level']
            current = result['current_price']
            distance = result['distance_pct']
            importance = result['importance']

            # Urgency indicator
            if distance < 0.5:
                urgency = "🚨 CRITICAL"
            elif distance < 1.0:
                urgency = "⚠️ VERY CLOSE"
            elif distance < 1.5:
                urgency = "⚡ CLOSE"
            else:
                urgency = "📊 APPROACHING"

            # Importance indicator
            if importance >= 70:
                imp_text = "🔥 HIGH"
            elif importance >= 50:
                imp_text = "📈 MEDIUM"
            else:
                imp_text = "📊 MODERATE"

            desc += f"**{i}. [{symbol}]({result['tradingview_link']})**\n"
            desc += f"💰 **Liquidation Level:** ${level:.6f} | **Current:** ${current:.6f}\n"
            desc += f"📏 **Distance:** {distance:.2f}% away ({urgency})\n"
            desc += f"🔥 **Importance:** {importance:.0f}% ({imp_text})\n"
            desc += f"💡 **Direction:** 🔴 SHORT REVERSAL (Price bounces DOWN or cascades)\n\n"

        embeds.append({
            "title": "🔴 5-Minute SHORT Scanner Results",
            "description": desc,
            "color": 0xFF0000,  # Red for short/sell
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Total opportunities: {len(results)} | Top {len(top_results)} shown"
            }
        })

        # Send to Discord
        try:
            payload = {"embeds": embeds}
            response = requests.post(
                DISCORD_WEBHOOK,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 204:
                logger.info(f"✅ Discord notification sent successfully")
            else:
                logger.error(f"❌ Discord error: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error sending Discord notification: {e}")

async def main():
    """Main function"""
    scanner = Quick5mShortScanner()
    results = await scanner.run_scan()
    scanner.send_discord_results(results)

    # Print summary
    print(f"\n{'='*60}")
    print(f"5-Minute SHORT Scan Results")
    print(f"{'='*60}")
    print(f"Total opportunities: {len(results)}\n")

    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['symbol']}")
        print(f"   Level: ${result['level']:.6f} | Current: ${result['current_price']:.6f}")
        print(f"   Distance: {result['distance_pct']:.2f}% | Importance: {result['importance']:.0f}%")
        print(f"   Link: {result['tradingview_link']}\n")

if __name__ == "__main__":
    asyncio.run(main())
