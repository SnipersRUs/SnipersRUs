#!/usr/bin/env python3
"""
One-time scan for coins that recently swept their 15-30 minute highs
"""

import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import time

DISCORD_WEBHOOK = ""

# Popular coins to scan
COINS_TO_SCAN = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "TRX", "LINK",
    "DOT", "MATIC", "SHIB", "LTC", "UNI", "ATOM", "ETC", "XLM", "ALGO",
    "VET", "ICP", "FIL", "APT", "ARB", "OP", "SUI", "SEI", "TIA", "INJ",
    "NEAR", "FTM", "AAVE", "MKR", "SNX", "COMP", "SUSHI", "CRV", "1INCH", "YFI"
]

def init_exchange():
    """Initialize exchange connection"""
    exchanges_to_try = ['coinbase', 'kraken', 'okx', 'bybit']

    for ex_name in exchanges_to_try:
        try:
            exchange_class = getattr(ccxt, ex_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
            exchange.load_markets()
            print(f"✅ Connected to {ex_name.upper()}")
            return exchange
        except Exception as e:
            print(f"⚠️ {ex_name} failed: {e}")
            continue

    print("❌ Failed to connect to any exchange")
    return None

def check_recent_high_sweep(exchange, symbol: str, timeframe: str, lookback: int):
    """Check if coin recently swept its high on given timeframe"""
    try:
        # Find symbol on exchange
        exchange_symbol = None
        for fmt in [f"{symbol}/USDT", f"{symbol}/USD", f"{symbol}USDT", symbol]:
            if fmt in exchange.markets:
                exchange_symbol = fmt
                break

        if not exchange_symbol:
            return None

        # Get current price
        ticker = exchange.fetch_ticker(exchange_symbol)
        current_price = float(ticker.get('last', 0))
        if current_price == 0:
            return None

        # Get candles for the timeframe
        ohlcv = exchange.fetch_ohlcv(exchange_symbol, timeframe, limit=lookback + 5)

        if not ohlcv or len(ohlcv) < lookback:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

        # Get recent high from lookback period (excluding last 2 bars to avoid false positives)
        if len(df) > lookback + 2:
            recent_high = df['high'].iloc[-lookback-2:-2].max()
        elif len(df) > 3:
            recent_high = df['high'].iloc[:-2].max()
        else:
            recent_high = df['high'].iloc[:-1].max() if len(df) > 1 else 0

        # Check if current or recent bars swept the recent high
        current_high = df['high'].iloc[-1]
        previous_high = df['high'].iloc[-2] if len(df) > 1 else 0

        # Sweep condition: current or previous high breaks above recent high
        # This catches sweeps that happened in the last 1-2 bars
        swept = (current_high > recent_high or previous_high > recent_high) and current_high >= recent_high

        if swept:
            # Calculate how much it swept
            sweep_amount = ((current_high - recent_high) / recent_high) * 100

            # Check volume
            avg_volume = df['volume'].iloc[-lookback:-1].mean() if len(df) > lookback else df['volume'].iloc[:-1].mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "current_high": current_high,
                "swept_high": recent_high,
                "sweep_amount_pct": sweep_amount,
                "volume_ratio": volume_ratio,
                "exchange_symbol": exchange_symbol
            }

        return None

    except Exception as e:
        print(f"  ⚠️ Error checking {symbol} {timeframe}: {e}")
        return None

def scan_high_sweeps():
    """Scan for coins that recently swept 15-30min highs"""
    exchange = init_exchange()
    if not exchange:
        return

    print(f"\n🔍 Scanning {len(COINS_TO_SCAN)} coins for recent 15-30min high sweeps...\n")

    sweeps_found = []

    for symbol in COINS_TO_SCAN:
        try:
            # Check 15min high sweep (lookback 20 bars = ~5 hours)
            sweep_15m = check_recent_high_sweep(exchange, symbol, '15m', lookback=20)
            if sweep_15m:
                sweep_15m['timeframe'] = '15m'
                sweeps_found.append(sweep_15m)
                print(f"  ✅ {symbol}: Swept 15m high (${sweep_15m['swept_high']:.4f} → ${sweep_15m['current_high']:.4f}, +{sweep_15m['sweep_amount_pct']:.2f}%)")

            # Check 30min high sweep (lookback 20 bars = ~10 hours)
            sweep_30m = check_recent_high_sweep(exchange, symbol, '30m', lookback=20)
            if sweep_30m:
                sweep_30m['timeframe'] = '30m'
                sweeps_found.append(sweep_30m)
                print(f"  ✅ {symbol}: Swept 30m high (${sweep_30m['swept_high']:.4f} → ${sweep_30m['current_high']:.4f}, +{sweep_30m['sweep_amount_pct']:.2f}%)")

            time.sleep(0.15)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️ Error scanning {symbol}: {e}")
            continue

    # Sort by sweep amount (largest first)
    sweeps_found.sort(key=lambda x: x['sweep_amount_pct'], reverse=True)

    # Limit to top 10
    sweeps_found = sweeps_found[:10]

    print(f"\n✅ Found {len(sweeps_found)} recent high sweeps\n")

    # Send to Discord
    send_results_to_discord(sweeps_found)

    return sweeps_found

def get_tradingview_link(symbol: str) -> str:
    """Generate TradingView chart link"""
    symbol_map = {
        "BTC": "KRAKEN:BTCUSDTPERP",
        "ETH": "KRAKEN:ETHUSDTPERP",
        "SOL": "KRAKEN:SOLUSDTPERP",
    }

    symbol_upper = symbol.upper()
    for key, tv_symbol in symbol_map.items():
        if key in symbol_upper:
            encoded = tv_symbol.replace(":", "%3A")
            return f"https://www.tradingview.com/chart/?symbol={encoded}"

    encoded = f"BINANCE%3A{symbol}USDT"
    return f"https://www.tradingview.com/chart/?symbol={encoded}"

def send_results_to_discord(sweeps: list):
    """Send high sweep results to Discord"""
    if not sweeps:
        embed = {
            "title": "📊 High Sweep Scan - Complete",
            "description": "**No recent high sweeps found**",
            "color": 0x0099FF,
            "fields": [
                {
                    "name": "ℹ️ Result",
                    "value": "No coins found that recently swept their 15-30 minute highs",
                    "inline": False
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Cloudflare Indicator Bot • High Sweep Scan"
            }
        }
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        return

    # Create main embed
    embed = {
        "title": f"📊 Recent High Sweeps - {len(sweeps)} Coins Found",
        "description": f"**Coins that recently swept their 15-30 minute highs**\n\n*Sorted by sweep amount (largest first)*",
        "color": 0xFFA500,  # Orange for sweeps
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": f"Cloudflare Indicator Bot • {len(sweeps)} high sweeps detected"
        }
    }

    # Add all sweeps found
    for i, sweep in enumerate(sweeps, 1):
        tv_link = get_tradingview_link(sweep['symbol'])
        chart_link = f"[View Chart]({tv_link})" if tv_link else ""

        field_value = (
            f"**Timeframe:** {sweep['timeframe']}\n"
            f"**Current Price:** ${sweep['current_price']:.4f}\n"
            f"**Swept High:** ${sweep['swept_high']:.4f}\n"
            f"**Sweep Amount:** +{sweep['sweep_amount_pct']:.2f}%\n"
            f"**Volume:** {sweep['volume_ratio']:.1f}x avg\n\n"
            f"{chart_link}"
        )

        embed["fields"].append({
            "name": f"#{i} {sweep['symbol']} - {sweep['timeframe']} Sweep",
            "value": field_value,
            "inline": True
        })

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Results sent to Discord!")
        else:
            print(f"❌ Discord error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending to Discord: {e}")

if __name__ == "__main__":
    print("🚀 Starting High Sweep Scan...")
    print("=" * 50)
    results = scan_high_sweeps()
    print("=" * 50)
    print("✅ Scan complete!")

