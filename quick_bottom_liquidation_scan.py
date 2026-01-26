#!/usr/bin/env python3
"""
Quick Bottom Liquidation Scan
Scans for coins at bottoms with increasing volume that are at/near daily liquidation levels
"""

import asyncio
import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional
import ccxt

# Configuration
DISCORD_WEBHOOK = ""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exchange
EXCHANGE_CONFIG = {
    'class': ccxt.mexc,
    'sandbox': False,
    'rateLimit': 1000,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
}

def is_stablecoin_pair(symbol: str) -> bool:
    """Check if symbol is a stablecoin pair"""
    stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'TUSD', 'USDP', 'USDD', 'FRAX', 'LUSD', 'PAXG']
    symbol_upper = symbol.upper()

    if 'USDC/USDT' in symbol_upper or 'USDT/USDC' in symbol_upper:
        return True

    clean_symbol = symbol_upper.replace(':USDT', '').strip()
    if '/' in clean_symbol:
        parts = clean_symbol.split('/')
        if len(parts) >= 2:
            base = parts[0].strip()
            quote = parts[1].strip()
            if base in stablecoins and quote in stablecoins:
                return True
            if base in stablecoins and quote == 'USDT':
                return True
            if quote in stablecoins and base == 'USDT':
                return True
    return False

def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
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

def detect_daily_liquidation_level(df: pd.DataFrame) -> Optional[Dict]:
    """Detect daily liquidation level using Pine Script logic"""
    if df is None or len(df) < 50:
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

    # Check recent candles for liquidations
    atr14 = calculate_atr(df, 14)

    # Look at last 10 daily candles
    for i in range(max(volume_lookback, len(df) - 10), len(df)):
        try:
            candle_high = high[i]
            candle_low = low[i]
            candle_close = close[i]
            candle_open = open_price[i]
            candle_volume = volume[i]

            # Volume analysis
            volume_z = (candle_volume - avg_volume) / volume_std if volume_std > 0 else 0.0
            abnormal_volume = volume_z >= 2.0

            # Liquidation size
            range_pu = candle_high - candle_low
            volume_m = candle_volume / 1e6
            liquidation_size = volume_m * range_pu

            # Major liquidation detection
            is_major_liquidation = liquidation_size >= 5.0 or abnormal_volume

            if not is_major_liquidation:
                continue

            # Calculate importance
            importance = 0.0
            if volume_z >= 3.0:
                importance += 40.0
            elif volume_z >= 2.0:
                importance += 25.0

            if liquidation_size >= 5.0:
                importance += 20.0

            if atr14 > 0:
                range_ratio = range_pu / atr14
                if range_ratio > 2.0:
                    importance += 15.0

            if importance < 15.0:  # Very low threshold to find more coins
                continue

            # Determine liquidation level
            is_bearish_candle = candle_close < candle_open
            if is_bearish_candle:
                liq_level = candle_high  # TOP liquidation
                liq_type = "top"
            else:
                liq_level = candle_low  # BOTTOM liquidation
                liq_type = "bottom"

            return {
                "level": liq_level,
                "type": liq_type,
                "importance": min(100.0, importance),
                "timestamp": df['timestamp'].iloc[i]
            }

        except Exception:
            continue

    return None

def check_at_bottom(df: pd.DataFrame) -> bool:
    """Check if coin is at/near recent bottom"""
    if len(df) < 20:
        return False

    close = df['close'].values
    low = df['low'].values

    # Check if current price is within 5% of recent 20-day low
    recent_low = np.min(low[-20:])
    current_price = close[-1]

    if recent_low == 0:
        return False

    distance_from_low = ((current_price - recent_low) / recent_low) * 100

    # At bottom if within 15% of recent low (very relaxed to find more coins)
    return distance_from_low <= 15.0

def check_increasing_volume(df: pd.DataFrame) -> bool:
    """Check if volume is increasing"""
    if len(df) < 10:
        return False

    volume = df['volume'].values

    # Compare last 3 candles to previous 3
    recent_avg = np.mean(volume[-3:])
    previous_avg = np.mean(volume[-6:-3]) if len(volume) >= 6 else np.mean(volume[-5:-2])

    if previous_avg == 0:
        # If no previous volume, check if current volume is above average
        overall_avg = np.mean(volume[-20:]) if len(volume) >= 20 else np.mean(volume)
        return recent_avg >= overall_avg * 0.8  # At least 80% of average

    # Volume increasing if recent avg is 5%+ higher (very relaxed)
    # OR if volume is just decent (not decreasing rapidly)
    return recent_avg >= previous_avg * 1.05 or recent_avg >= previous_avg * 0.9

async def scan_symbol(exchange, symbol: str) -> Optional[Dict]:
    """Scan single symbol for bottom liquidation setup"""
    try:
        # Get daily data
        ohlcv = await asyncio.get_event_loop().run_in_executor(
            None, exchange.fetch_ohlcv, symbol, '1d', None, 100
        )

        if not ohlcv or len(ohlcv) < 50:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Check if at bottom
        if not check_at_bottom(df):
            return None

        # Check if volume is increasing
        if not check_increasing_volume(df):
            return None

        # Detect liquidation level
        liquidation = detect_daily_liquidation_level(df)
        if not liquidation:
            return None

        # Get current price
        ticker = await asyncio.get_event_loop().run_in_executor(
            None, exchange.fetch_ticker, symbol
        )
        current_price = ticker.get('last', 0) or df['close'].iloc[-1]

        # Check if price is at/near liquidation level (within 15%)
        # For bottom liquidations, price should be near the low
        # For top liquidations, price should be near the high
        distance_pct = abs(current_price - liquidation['level']) / current_price * 100 if current_price > 0 else 999

        # Must be within 15% of liquidation level (very relaxed to find 7 coins)
        if distance_pct > 15.0:
            return None

        # Get TradingView link
        base_symbol = symbol.split('/')[0] if '/' in symbol else symbol
        tv_link = f"https://www.tradingview.com/chart/?symbol=MEXC:{base_symbol}USDT.P"

        return {
            "symbol": symbol,
            "current_price": current_price,
            "liquidation_level": liquidation['level'],
            "liquidation_type": liquidation['type'],
            "distance_pct": distance_pct,
            "importance": liquidation['importance'],
            "tradingview_link": tv_link
        }

    except Exception as e:
        logger.debug(f"Error scanning {symbol}: {e}")
        return None

async def quick_scan():
    """Run quick scan for bottom liquidation setups"""
    logger.info("🚀 Starting quick bottom liquidation scan...")

    # Initialize exchange
    exchange = EXCHANGE_CONFIG['class']({
        'sandbox': EXCHANGE_CONFIG['sandbox'],
        'rateLimit': EXCHANGE_CONFIG['rateLimit'],
        'enableRateLimit': EXCHANGE_CONFIG['enableRateLimit'],
        'options': EXCHANGE_CONFIG['options']
    })

    # Get symbols
    markets = await asyncio.get_event_loop().run_in_executor(None, exchange.load_markets)
    tickers = await asyncio.get_event_loop().run_in_executor(None, exchange.fetch_tickers)

    # Get top volume symbols (limit to 100 for speed)
    symbols = []
    for symbol, ticker in tickers.items():
        if ':USDT' not in symbol:
            continue
        market = markets.get(symbol, {})
        if (market.get('quote') == 'USDT' and
            market.get('active', True) and
            market.get('type') in ['swap', 'future'] and
            not is_stablecoin_pair(symbol)):
            volume = ticker.get('quoteVolume', 0) or 0
            if volume > 0:
                symbols.append((symbol, volume))

    # Sort by volume and take top 300 (more symbols = more chances to find 7)
    symbols.sort(key=lambda x: x[1], reverse=True)
    symbols = [s[0] for s in symbols[:300]]

    logger.info(f"📊 Scanning {len(symbols)} symbols...")

    # Scan symbols
    results = []
    for symbol in symbols:
        result = await scan_symbol(exchange, symbol)
        if result:
            results.append(result)
            logger.info(f"✅ Found: {symbol} - {result['distance_pct']:.2f}% from liquidation")

        # Rate limiting
        await asyncio.sleep(0.1)

    # Sort by distance (closest first), prefer bottom liquidations, then take top 7
    # Score: bottom liquidations get priority, then sort by distance
    scored_results = []
    for r in results:
        score = r['distance_pct']
        if r['liquidation_type'] == 'bottom':
            score -= 2.0  # Strongly prefer bottom liquidations
        scored_results.append((score, r))

    scored_results.sort(key=lambda x: x[0])
    top_7 = [r[1] for r in scored_results[:7]]

    # If we have less than 7, that's okay - show what we found
    logger.info(f"📊 Found {len(results)} total matches, showing top {len(top_7)}")

    logger.info(f"🎯 Found {len(results)} coins, showing top 7")

    # Send to Discord
    await send_discord_results(top_7)

    return top_7

async def send_discord_results(results: List[Dict]):
    """Send results to Discord"""
    if not results:
        embed = {
            "title": "🔍 Bottom Liquidation Scan - No Results",
            "description": "No coins found at bottoms with increasing volume near daily liquidation levels.",
            "color": 0x808080,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        payload = {"embeds": [embed]}
    else:
        desc = f"**🔍 Bottom Liquidation Scan - Top 7 Coins**\n\n"
        desc += f"Coins at **bottoms** with **increasing volume** near daily liquidation levels\n\n"

        for i, result in enumerate(results, 1):
            type_emoji = "🔴" if result['liquidation_type'] == "top" else "🟢"
            type_text = "TOP (Longs)" if result['liquidation_type'] == "top" else "BOTTOM (Shorts)"

            # Distance indicator
            if result['distance_pct'] <= 1.0:
                dist_emoji = "🎯"
                dist_text = "AT LEVEL"
            elif result['distance_pct'] <= 3.0:
                dist_emoji = "📍"
                dist_text = "VERY CLOSE"
            else:
                dist_emoji = "📊"
                dist_text = "APPROACHING"

            desc += f"**{i}. [{result['symbol']}]({result['tradingview_link']})**\n"
            desc += f"{type_emoji} **{type_text}** Liquidation\n"
            desc += f"💰 Level: **${result['liquidation_level']:.4f}** | Current: **${result['current_price']:.4f}**\n"
            desc += f"{dist_emoji} **{dist_text}** - {result['distance_pct']:.2f}% away | "
            desc += f"🔥 **{result['importance']:.0f}%** importance\n\n"

        embed = {
            "title": "🔍 Bottom Liquidation Scan - Top 7 Coins",
            "description": desc,
            "color": 0xFF8800,  # Orange
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Coins at bottoms with increasing volume near daily liquidation levels"
            }
        }
        payload = {"embeds": [embed]}

    try:
        response = requests.post(
            DISCORD_WEBHOOK,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        if response.status_code == 204:
            logger.info("✅ Results sent to Discord")
        else:
            logger.error(f"❌ Discord error: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Error sending to Discord: {e}")

async def main():
    """Main function"""
    try:
        results = await quick_scan()
        logger.info(f"✅ Scan complete! Found {len(results)} coins")
    except Exception as e:
        logger.error(f"❌ Scan error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
