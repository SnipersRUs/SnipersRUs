#!/usr/bin/env python3
"""
One-time script to scan coins at Monthly Golden Pockets and send top 10 to Discord
"""
import ccxt
import pandas as pd
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Discord webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr"

# Minimum volume
MIN_VOLUME_24H_USD = 500000


def calculate_gps_zones(high: float, low: float) -> Dict[str, float]:
    """Calculate Golden Pocket zones (0.618-0.65 Fibonacci retracement)"""
    gp_high = high - (high - low) * 0.618
    gp_low = high - (high - low) * 0.65
    return {'gp_high': gp_high, 'gp_low': gp_low}


def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str, limit: int = 200) -> Optional[pd.DataFrame]:
    """Fetch OHLCV data"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        return None


def get_futures_pairs(exchange: ccxt.Exchange) -> List[str]:
    """Get all MEXC futures pairs with sufficient volume"""
    pairs = []
    try:
        tickers = exchange.fetch_tickers()
        for symbol, market in exchange.markets.items():
            if (market.get('type') == 'swap' and
                market.get('active', True) and
                market.get('quote') == 'USDT'):

                ticker = tickers.get(symbol)
                if ticker:
                    volume_24h = ticker.get('quoteVolume', 0) or 0
                    if volume_24h >= MIN_VOLUME_24H_USD:
                        pairs.append(symbol)

        print(f"📊 Found {len(pairs)} MEXC futures pairs with volume > ${MIN_VOLUME_24H_USD:,.0f}")
        return pairs
    except Exception as e:
        print(f"Error fetching futures pairs: {e}")
        return []


def scan_monthly_golden_pockets(exchange: ccxt.Exchange, pairs: List[str]) -> List[Dict]:
    """Scan for coins at monthly golden pockets"""
    results = []

    print(f"🔍 Scanning {len(pairs)} pairs for Monthly Golden Pockets...")

    for i, symbol in enumerate(pairs):
        if (i + 1) % 50 == 0:
            print(f"   Progress: {i + 1}/{len(pairs)} pairs scanned...")

        try:
            # Fetch monthly data
            df_monthly = fetch_ohlcv(exchange, symbol, '1M', limit=12)
            if df_monthly is None or len(df_monthly) < 1:
                continue

            # Get current price (15m)
            df_15m = fetch_ohlcv(exchange, symbol, '15m', limit=10)
            if df_15m is None or len(df_15m) < 1:
                continue

            current_price = df_15m['close'].iloc[-1]

            # Calculate monthly golden pocket
            monthly_high = df_monthly['high'].max()
            monthly_low = df_monthly['low'].min()

            if monthly_high <= monthly_low:
                continue

            gps_zones = calculate_gps_zones(monthly_high, monthly_low)
            gp_high = gps_zones['gp_high']
            gp_low = gps_zones['gp_low']

            # Check if price is BELOW monthly GP (treating GP as RESISTANCE)
            # Price should be approaching GP from below (within 5% of GP zone)
            gp_center = (gp_high + gp_low) / 2

            # Price must be BELOW the GP zone (approaching resistance)
            if current_price < gp_high:
                # Calculate distance from GP zone
                distance_from_gp_low = gp_low - current_price
                distance_pct = (distance_from_gp_low / gp_low * 100) if gp_low > 0 else 999

                # Include coins within 10% below GP zone (approaching resistance)
                if distance_pct <= 10.0 and distance_pct >= 0:
                    # Get volume for sorting
                    ticker = exchange.fetch_ticker(symbol)
                    volume_24h = ticker.get('quoteVolume', 0) or 0

                    # Calculate how close to GP
                    if current_price >= gp_low:
                        status = "AT/NEAR GP LOW (Resistance)"
                        distance_to_resistance = 0
                    else:
                        distance_to_resistance = distance_pct
                        status = f"{distance_pct:.2f}% BELOW GP (Approaching Resistance)"

                    # Check recent price action (is it rallying up to resistance?)
                    if len(df_15m) >= 5:
                        recent_prices = df_15m['close'].tail(5).values
                        price_trend = "Rallying" if recent_prices[-1] > recent_prices[0] else "Consolidating"
                    else:
                        price_trend = "Unknown"

                    results.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'gp_high': gp_high,
                        'gp_low': gp_low,
                        'gp_center': gp_center,
                        'distance_pct': distance_to_resistance,
                        'status': status,
                        'price_trend': price_trend,
                        'monthly_high': monthly_high,
                        'monthly_low': monthly_low,
                        'volume_24h': volume_24h,
                        'chart_url': f"https://www.tradingview.com/chart/?symbol=MEXC:{symbol.replace('/', '').replace(':USDT', 'USDT')}"
                    })

        except Exception as e:
            continue

    # Sort by volume (highest first) and take top 10
    results.sort(key=lambda x: x['volume_24h'], reverse=True)
    return results[:10]


def send_to_discord(coins: List[Dict]):
    """Send monthly GP coins to Discord in orange card"""
    if not coins:
        print("❌ No coins found at monthly golden pockets")
        return

    embed = {
        "title": f"📊 Monthly GP as RESISTANCE - Top {len(coins)} Coins",
        "color": 0xFFA500,  # Orange
        "description": "Coins approaching Monthly Golden Pocket from BELOW (GP acting as RESISTANCE) - Potential SHORT opportunities",
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    for i, coin in enumerate(coins, 1):
        field_value = f"**Price:** ${coin['current_price']:.6f}\n"
        field_value += f"**Status:** {coin['status']}\n"
        field_value += f"**Price Trend:** {coin.get('price_trend', 'Unknown')}\n"
        field_value += f"**Monthly GP Zone (Resistance):** ${coin['gp_low']:.6f} - ${coin['gp_high']:.6f}\n"
        field_value += f"**Distance to Resistance:** {coin['distance_pct']:.2f}%\n"
        field_value += f"**Monthly Range:** ${coin['monthly_low']:.6f} - ${coin['monthly_high']:.6f}\n"
        field_value += f"**24h Volume:** ${coin['volume_24h']:,.0f}\n"
        field_value += f"\n[Chart]({coin['chart_url']})"

        embed["fields"].append({
            "name": f"{i}. {coin['symbol']}",
            "value": field_value,
            "inline": False
        })

    try:
        payload = {"embeds": [embed]}
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        r.raise_for_status()
        print(f"✅ Sent {len(coins)} coins to Discord")
    except Exception as e:
        print(f"❌ Failed to send to Discord: {e}")


def main():
    """Main function"""
    print("🚀 Starting Monthly Golden Pocket scan...")

    # Initialize exchange
    exchange = ccxt.mexc({
        'apiKey': '',
        'secret': '',
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })

    # Get futures pairs
    pairs = get_futures_pairs(exchange)
    if not pairs:
        print("❌ No pairs found")
        return

    # Scan for monthly golden pockets (as resistance)
    coins = scan_monthly_golden_pockets(exchange, pairs)

    if coins:
        print(f"\n✅ Found {len(coins)} coins approaching Monthly GP as RESISTANCE")
        for coin in coins:
            print(f"   - {coin['symbol']}: ${coin['current_price']:.6f} ({coin['status']}) - Volume: ${coin['volume_24h']:,.0f}")

        # Send to Discord
        send_to_discord(coins)
    else:
        print("❌ No coins found approaching monthly GP as resistance")


if __name__ == "__main__":
    main()
