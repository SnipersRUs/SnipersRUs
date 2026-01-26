#!/usr/bin/env python3
"""
Scan for high probability short opportunities
Looks for: overbought conditions, resistance levels, bearish divergences, etc.
"""

import ccxt
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
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

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_vwap(df: pd.DataFrame) -> float:
    """Calculate VWAP"""
    if df is None or len(df) == 0:
        return None
    typical_price = (df['high'] + df['low'] + df['close']) / 3.0
    pv_sum = (typical_price * df['volume']).sum()
    v_sum = df['volume'].sum()
    if v_sum == 0:
        return None
    return pv_sum / v_sum

def calculate_indicators(df: pd.DataFrame):
    """Calculate all indicators for short analysis"""
    if len(df) < 50:
        return None

    # RSI
    rsi = calculate_rsi(df, 14)
    current_rsi = rsi.iloc[-1]

    # Moving Averages
    ma20 = df['close'].rolling(20).mean()
    ma50 = df['close'].rolling(50).mean()
    ma200 = df['close'].rolling(200).mean()

    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()

    # VWAP (daily)
    daily_vwap = calculate_vwap(df.tail(20))

    # Price position
    current_price = df['close'].iloc[-1]
    price_above_ma20 = current_price > ma20.iloc[-1] if len(ma20) > 0 else False
    price_above_ma50 = current_price > ma50.iloc[-1] if len(ma50) > 0 else False
    price_above_ma200 = current_price > ma200.iloc[-1] if len(ma200) > 0 else False

    # Distance from VWAP
    distance_from_vwap = ((current_price - daily_vwap) / daily_vwap * 100) if daily_vwap else 0

    # Volume analysis
    avg_volume = df['volume'].rolling(20).mean()
    volume_ratio = df['volume'].iloc[-1] / avg_volume.iloc[-1] if len(avg_volume) > 0 else 1

    # Recent price action
    price_change_1d = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0
    price_change_7d = ((df['close'].iloc[-1] - df['close'].iloc[-7]) / df['close'].iloc[-7] * 100) if len(df) >= 7 else 0

    # Bearish divergence check (simplified)
    price_higher = df['high'].iloc[-1] > df['high'].iloc[-5] if len(df) >= 5 else False
    rsi_lower = rsi.iloc[-1] < rsi.iloc[-5] if len(rsi) >= 5 else False
    bearish_divergence = price_higher and rsi_lower and current_rsi > 60

    # MACD bearish
    macd_bearish = macd.iloc[-1] < macd_signal.iloc[-1] if len(macd) > 0 and len(macd_signal) > 0 else False

    return {
        'rsi': current_rsi,
        'price': current_price,
        'distance_from_vwap': distance_from_vwap,
        'volume_ratio': volume_ratio,
        'price_change_1d': price_change_1d,
        'price_change_7d': price_change_7d,
        'bearish_divergence': bearish_divergence,
        'macd_bearish': macd_bearish,
        'price_above_ma20': price_above_ma20,
        'price_above_ma50': price_above_ma50,
        'price_above_ma200': price_above_ma200,
        'daily_vwap': daily_vwap
    }

def score_short_opportunity(indicators: dict) -> dict:
    """Score short opportunity based on multiple factors"""
    score = 0
    reasons = []

    # RSI overbought (70+)
    if indicators['rsi'] >= 70:
        score += 30
        reasons.append(f"RSI {indicators['rsi']:.1f} (overbought)")
    elif indicators['rsi'] >= 65:
        score += 20
        reasons.append(f"RSI {indicators['rsi']:.1f} (approaching overbought)")
    elif indicators['rsi'] >= 60:
        score += 10
        reasons.append(f"RSI {indicators['rsi']:.1f} (elevated)")

    # Price significantly above VWAP
    if indicators['distance_from_vwap'] > 5:
        score += 25
        reasons.append(f"{indicators['distance_from_vwap']:.1f}% above VWAP")
    elif indicators['distance_from_vwap'] > 3:
        score += 15
        reasons.append(f"{indicators['distance_from_vwap']:.1f}% above VWAP")
    elif indicators['distance_from_vwap'] > 1:
        score += 8
        reasons.append(f"{indicators['distance_from_vwap']:.1f}% above VWAP")

    # Bearish divergence
    if indicators['bearish_divergence']:
        score += 20
        reasons.append("Bearish divergence")

    # MACD bearish
    if indicators['macd_bearish']:
        score += 10
        reasons.append("MACD bearish")

    # Strong recent rally (potential exhaustion)
    if indicators['price_change_7d'] > 15:
        score += 20
        reasons.append(f"+{indicators['price_change_7d']:.1f}% in 7d (exhaustion)")
    elif indicators['price_change_7d'] > 10:
        score += 15
        reasons.append(f"+{indicators['price_change_7d']:.1f}% in 7d")
    elif indicators['price_change_7d'] > 5:
        score += 8
        reasons.append(f"+{indicators['price_change_7d']:.1f}% in 7d")

    # Volume declining on up move (weakness)
    if indicators['price_change_1d'] > 0 and indicators['volume_ratio'] < 0.8:
        score += 10
        reasons.append("Low volume on up move")

    # Price above all MAs but showing weakness
    if indicators['price_above_ma20'] and indicators['price_above_ma50'] and indicators['rsi'] > 70:
        score += 10
        reasons.append("Above MAs but overbought")

    # Negative momentum (price up but indicators weakening)
    if indicators['price_change_1d'] > 2 and indicators['rsi'] < indicators.get('rsi_prev', indicators['rsi']):
        score += 8
        reasons.append("Momentum weakening")

    # High volume on down days (distribution)
    if indicators['price_change_1d'] < 0 and indicators['volume_ratio'] > 1.5:
        score += 12
        reasons.append("High volume on down move")

    return {
        'score': score,
        'reasons': reasons,
        'grade': 'A+' if score >= 60 else 'A' if score >= 50 else 'B' if score >= 40 else 'C' if score >= 30 else 'D'
    }

def scan_short_opportunities():
    """Scan for high probability short opportunities"""
    exchange = init_exchange()
    if not exchange:
        return

    print(f"\n🔍 Scanning {len(COINS_TO_SCAN)} coins for short opportunities...\n")

    short_opportunities = []

    for symbol in COINS_TO_SCAN:
        try:
            # Find symbol on exchange
            exchange_symbol = None
            for fmt in [f"{symbol}/USDT", f"{symbol}/USD", f"{symbol}USDT", symbol]:
                if fmt in exchange.markets:
                    exchange_symbol = fmt
                    break

            if not exchange_symbol:
                continue

            # Get hourly data for analysis
            ohlcv = exchange.fetch_ohlcv(exchange_symbol, '1h', limit=500)

            if not ohlcv or len(ohlcv) < 50:
                continue

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

            # Calculate indicators
            indicators = calculate_indicators(df)
            if not indicators:
                continue

            # Score short opportunity
            short_score = score_short_opportunity(indicators)

            # Only include high probability shorts (score >= 20)
            if short_score['score'] >= 20:
                short_opportunities.append({
                    "symbol": symbol,
                    "price": indicators['price'],
                    "rsi": indicators['rsi'],
                    "distance_from_vwap": indicators['distance_from_vwap'],
                    "price_change_7d": indicators['price_change_7d'],
                    "score": short_score['score'],
                    "grade": short_score['grade'],
                    "reasons": short_score['reasons'],
                    "exchange_symbol": exchange_symbol
                })
                print(f"  ✅ {symbol}: Score {short_score['score']} ({short_score['grade']}) - {', '.join(short_score['reasons'][:2])}")

            time.sleep(0.1)  # Rate limiting

        except Exception as e:
            print(f"  ⚠️ Error scanning {symbol}: {e}")
            continue

    # Sort by score (highest first)
    short_opportunities.sort(key=lambda x: x['score'], reverse=True)

    print(f"\n✅ Found {len(short_opportunities)} high probability short opportunities\n")

    # Send to Discord
    send_results_to_discord(short_opportunities)

    return short_opportunities

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

def send_results_to_discord(opportunities: list):
    """Send short opportunities to Discord"""
    if not opportunities:
        embed = {
            "title": "🔴 Short Opportunities Scan - Complete",
            "description": "**No high probability short opportunities found**",
            "color": 0x800080,  # Purple
            "fields": [
                {
                    "name": "ℹ️ Result",
                    "value": "No coins met the criteria for high probability short setups",
                    "inline": False
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": "Cloudflare Indicator Bot • Short Scanner"
            }
        }
        requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        return

    # Create main embed
    embed = {
        "title": f"🔴 High Probability Short Opportunities - {len(opportunities)} Found",
        "description": f"**Top short setups** sorted by probability score\n\n*Based on: RSI, VWAP distance, divergences, momentum*",
        "color": 0x800080,  # Purple for shorts
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": f"Cloudflare Indicator Bot • {len(opportunities)} short opportunities"
        }
    }

    # Add top opportunities
    top_opportunities = opportunities[:10]
    for i, opp in enumerate(top_opportunities, 1):
        tv_link = get_tradingview_link(opp['symbol'])
        chart_link = f"[View Chart]({tv_link})" if tv_link else ""

        reasons_text = "\n".join([f"• {r}" for r in opp['reasons'][:3]])

        field_value = (
            f"**Grade:** {opp['grade']} (Score: {opp['score']})\n"
            f"**Price:** ${opp['price']:.4f}\n"
            f"**RSI:** {opp['rsi']:.1f}\n"
            f"**7d Change:** +{opp['price_change_7d']:.1f}%\n"
            f"**VWAP Distance:** +{opp['distance_from_vwap']:.1f}%\n\n"
            f"**Reasons:**\n{reasons_text}\n\n"
            f"{chart_link}"
        )

        embed["fields"].append({
            "name": f"#{i} {opp['symbol']} 🔴 SHORT",
            "value": field_value,
            "inline": False
        })

    # If more than 10, add summary
    if len(opportunities) > 10:
        remaining = opportunities[10:]
        remaining_text = ", ".join([f"{o['symbol']} ({o['grade']})" for o in remaining[:10]])
        embed["fields"].append({
            "name": f"➕ {len(remaining)} More Opportunities",
            "value": remaining_text[:1024],
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
    print("🚀 Starting Short Opportunities Scan...")
    print("=" * 50)
    results = scan_short_opportunities()
    print("=" * 50)
    print("✅ Scan complete!")

