#!/usr/bin/env python3
"""
One-time scan for coins trading ABOVE their weekly VWAP
"""

import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import time

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

# Popular coins to scan
COINS_TO_SCAN = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "TRX", "LINK",
    "DOT", "MATIC", "SHIB", "DAI", "LTC", "UNI", "ATOM", "ETC", "XLM", "ALGO",
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

def calculate_weekly_vwap(df: pd.DataFrame) -> float:
    """Calculate Weekly VWAP"""
    if df is None or len(df) == 0:
        return None

    # Calculate typical price
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0

    # Calculate VWAP: sum(typical_price * volume) / sum(volume)
    pv_sum = (typical_price * df['volume']).sum()
    v_sum = df['volume'].sum()

    if v_sum == 0:
        return None

    vwap = pv_sum / v_sum
    return vwap

def scan_coins_above_weekly_vwap():
    """Scan coins that are trading above their weekly VWAP"""
    exchange = init_exchange()
    if not exchange:
        return

    print(f"\n🔍 Scanning {len(COINS_TO_SCAN)} coins for Weekly VWAP...\n")

    coins_above_vwap = []

    for symbol in COINS_TO_SCAN:
        try:
            # Try to find symbol on exchange
            exchange_symbol = None
            # Try different formats
            for fmt in [f"{symbol}/USDT", f"{symbol}/USD", f"{symbol}USDT", symbol]:
                if fmt in exchange.markets:
                    exchange_symbol = fmt
                    break

            if not exchange_symbol:
                continue

            # Get current price
            ticker = exchange.fetch_ticker(exchange_symbol)
            current_price = float(ticker.get('last', 0))

            if current_price == 0:
                continue

            # Get hourly candles for the current week (7 days = 168 hours)
            # Use daily candles for weekly VWAP (7 days)
            ohlcv = exchange.fetch_ohlcv(exchange_symbol, '1d', limit=10)

            if not ohlcv or len(ohlcv) < 7:
                continue

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

            # Get last 7 days for weekly VWAP
            now = datetime.now(timezone.utc)
            week_ago = now - timedelta(days=7)
            df_week = df[df['timestamp'] >= week_ago]

            if len(df_week) == 0:
                # If no data for current week, use last 7 candles
                df_week = df.tail(7)

            # Calculate Weekly VWAP
            weekly_vwap = calculate_weekly_vwap(df_week)

            if weekly_vwap is None or weekly_vwap == 0:
                continue

            # Check if current price is above Weekly VWAP
            if current_price > weekly_vwap:
                distance_pct = ((current_price - weekly_vwap) / weekly_vwap) * 100
                coins_above_vwap.append({
                    "symbol": symbol,
                    "current_price": current_price,
                    "weekly_vwap": weekly_vwap,
                    "distance_pct": distance_pct,
                    "exchange_symbol": exchange_symbol
                })
                print(f"  ✅ {symbol}: ${current_price:.4f} > Weekly VWAP ${weekly_vwap:.4f} ({distance_pct:.2f}% above)")

            time.sleep(0.1)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️ Error scanning {symbol}: {e}")
            continue

    # Sort by distance from VWAP (furthest above first)
    coins_above_vwap.sort(key=lambda x: x['distance_pct'], reverse=True)

    print(f"\n✅ Found {len(coins_above_vwap)} coins above Weekly VWAP\n")

    # Send to Discord
    send_results_to_discord(coins_above_vwap)

    return coins_above_vwap

def get_tradingview_link(symbol: str) -> str:
    """Generate TradingView chart link"""
    # Use Kraken perps as requested
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

    # Fallback to Binance spot
    encoded = f"BINANCE%3A{symbol}USDT"
    return f"https://www.tradingview.com/chart/?symbol={encoded}"

def send_results_to_discord(coins: list):
    """Send scan results to Discord"""
    if not coins:
        embed = {
            "title": "📊 Weekly VWAP Scan - Complete",
            "description": "**No coins found above Weekly VWAP**",
            "color": 0x0099FF,
            "fields": [
                {
                    "name": "ℹ️ Result",
                    "value": "All scanned coins are trading at or below their Weekly VWAP",
                    "inline": False
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Cloudflare Indicator Bot • Weekly VWAP Scan"
            }
        }

        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        return

    # Create main embed
    embed = {
        "title": f"📊 Weekly VWAP Scan - {len(coins)} Coins Above VWAP",
        "description": f"**Coins currently trading above their Weekly VWAP**\n\n*Sorted by distance from VWAP (furthest above first)*",
        "color": 0x00FF00,  # Green for bullish
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": f"Cloudflare Indicator Bot • {len(coins)} coins above weekly VWAP"
        }
    }

    # Add top 10 coins (Discord embed limit)
    top_coins = coins[:10]
    for i, coin in enumerate(top_coins, 1):
        tv_link = get_tradingview_link(coin['symbol'])
        chart_link = f"[View Chart]({tv_link})" if tv_link else ""

        field_value = (
            f"**Price:** ${coin['current_price']:.4f}\n"
            f"**Weekly VWAP:** ${coin['weekly_vwap']:.4f}\n"
            f"**Distance:** {coin['distance_pct']:.2f}% above\n"
            f"{chart_link}"
        )

        embed["fields"].append({
            "name": f"#{i} {coin['symbol']}",
            "value": field_value,
            "inline": True
        })

    # If more than 10 coins, add summary
    if len(coins) > 10:
        remaining = coins[10:]
        remaining_text = ", ".join([f"{c['symbol']} (+{c['distance_pct']:.1f}%)" for c in remaining[:10]])
        embed["fields"].append({
            "name": f"➕ {len(remaining)} More Coins",
            "value": remaining_text[:1024],  # Discord field limit
            "inline": False
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
    print("🚀 Starting Weekly VWAP Scan...")
    print("=" * 50)
    results = scan_coins_above_weekly_vwap()
    print("=" * 50)
    print("✅ Scan complete!")

