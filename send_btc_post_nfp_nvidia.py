#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Post-NFP & NVIDIA Update
Sends BTC analysis as a purple embed card to Discord
"""

import requests
import sys

def send_btc_post_nfp_nvidia():
    """Send the BTC post-NFP & NVIDIA update to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = ""

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "🚨 BTC POST-NFP & NVIDIA UPDATE - NOV 20, 2025 🚨",
        "description": "**Current Price:** $91,329 | Critical Support Test",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "⚡ BREAKING DATA RECAP",
                "value": (
                    "**📊 NFP (8:30 AM):**\n"
                    "• 119,000 jobs (vs 50k expected) - HUGE BEAT\n"
                    "• Unemployment 4.4% (vs 4.3% expected) - ROSE\n"
                    "• Result: Mixed - strong jobs BUT rising unemployment\n\n"
                    "**📊 NVIDIA (4:30 PM Yesterday):**\n"
                    "• Revenue: $57B (vs $54.9B expected) - BEAT\n"
                    "• EPS: $1.30 (vs $1.25 expected) - BEAT\n"
                    "• Q4 Guidance: $65B (vs $61.7B expected) - SMASHED\n"
                    "• Stock: +4% after-hours\n"
                    "• Result: BULLISH for risk assets\n\n"
                    "**💎 BTC REACTION:**\n"
                    "• Reclaimed $90k during Nvidia call\n"
                    "• Now consolidating $90.8k-$92.2k\n"
                    "• At CRITICAL channel support"
                ),
                "inline": False
            },
            {
                "name": "📊 CRITICAL LEVELS",
                "value": (
                    "🔴 **RESISTANCE:**\n"
                    "$92,200 (purple box top) | $92,800-$93,000 | $94,000 | $96,000-$98,000\n\n"
                    "🟢 **SUPPORT:**\n"
                    "$90,800 (purple box bottom) ⚠️ **CRITICAL**\n"
                    "$90,000 (psychological + wick low)\n"
                    "$88,500-$89,000 (channel support)\n"
                    "$87,500-$88,000 (if channel breaks)\n\n"
                    "⚠️ **THE LINE: $90,800**\n"
                    "Break below = cascade to $88k likely\n"
                    "Hold above = bounce to $94k-$96k possible"
                ),
                "inline": False
            },
            {
                "name": "🟢 LONG #1: Channel Support (65% win)",
                "value": (
                    "📍 Entry: $90,500-$91,000 (NOW)\n"
                    "🛑 Stop: $89,800\n"
                    "🎯 Targets: $92.5k / $94k / $96k\n"
                    "💡 Best R/R of the week\n"
                    "✅ Confirmation: 4H close > $91.5k"
                ),
                "inline": False
            },
            {
                "name": "🟢 LONG #2: Breakout (55% win)",
                "value": (
                    "📍 Entry: $92,800-$93,000 (on break)\n"
                    "🛑 Stop: $91,500\n"
                    "🎯 Targets: $94.5k / $96k / $98k\n"
                    "💡 Wait for clean break + retest\n"
                    "✅ Confirmation: Volume spike + reclaim $92.8k"
                ),
                "inline": False
            },
            {
                "name": "🔴 SHORT: Failed Rally (60% win)",
                "value": (
                    "📍 Entry: $92,500-$93,000\n"
                    "🛑 Stop: $93,800\n"
                    "🎯 Targets: $90.5k / $89k / $87.5k\n"
                    "💡 Multiple rejections expected\n"
                    "✅ Confirmation: Wick at $93k + volume"
                ),
                "inline": False
            },
            {
                "name": "🎲 NEXT 24-48H PROBABILITIES",
                "value": (
                    "• 40% → Relief rally to $94k-$96k (Nvidia bullish + risk-on)\n"
                    "• 35% → Failed bounce to $88k-$90k (NFP kills Dec rate cut hopes)\n"
                    "• 25% → Range chop $90k-$93k (Mixed data = mixed sentiment)\n\n"
                    "**Directional Bias:**\n"
                    "• Next 48h: Neutral (50/50)\n"
                    "• This Week: Slightly bullish (55/45)\n"
                    "• Rest of Nov: Depends on $90k hold"
                ),
                "inline": False
            },
            {
                "name": "📅 THIS WEEK'S EVENTS",
                "value": (
                    "**TODAY (Thu Nov 20):** Digesting NFP + Nvidia data | Market consolidation\n"
                    "**FRIDAY (Nov 21):** End of week positioning | Watch for Friday close volatility\n"
                    "**WEEKEND:** Low liquidity expected | Monitor for gap moves\n\n"
                    "⚠️ **NOTE:** Monitor volume and volatility patterns heading into weekend"
                ),
                "inline": False
            },
            {
                "name": "⚠️ BEARISH SIGNALS",
                "value": (
                    "• Dec Fed rate cut odds FALLING (NFP strong)\n"
                    "• BTC down 30% from $126k ATH\n"
                    "• Death cross still active\n"
                    "• Channel support at risk\n"
                    "• Fear & Greed: Still Extreme Fear"
                ),
                "inline": False
            },
            {
                "name": "✅ BULLISH SIGNALS",
                "value": (
                    "• Nvidia CRUSHED earnings = risk-on\n"
                    "• BTC reclaimed $90k (Nvidia call)\n"
                    "• At major channel support ($88k-$91k)\n"
                    "• Extremely oversold (RSI <30)\n"
                    "• Rising unemployment = Fed may still cut\n"
                    "• November historically strong for BTC"
                ),
                "inline": False
            },
            {
                "name": "🎯 FED IMPACT",
                "value": (
                    "• NFP beat = hawkish Fed = bearish BTC\n"
                    "• BUT rising unemployment = dovish Fed = bullish BTC\n"
                    "• Net effect: MIXED/NEUTRAL\n"
                    "• December rate cut: 45% odds (down from 60%)"
                ),
                "inline": False
            },
            {
                "name": "💡 TRADING WISDOM",
                "value": (
                    "✅ **DO:** Use SMALL size (1-2% risk max) | Set tight stops | Take profits early\n"
                    "❌ **DON'T:** Trade large size | Chase pumps | FOMO into wicks\n\n"
                    "**🎯 BEST STRATEGY:**\n"
                    "1. Long $90.5k-$91k with $89.8k stop\n"
                    "2. Target $92.5k-$94k (take partials)\n"
                    "3. If we break $90k, cut and wait for $88k\n"
                    "4. Monitor volume and price action closely"
                ),
                "inline": False
            },
            {
                "name": "🔗 KEY LINKS",
                "value": (
                    "[NFP Data](https://www.bls.gov/news.release/empsit.nr0.htm) | "
                    "[Nvidia Earnings](https://www.cnbc.com/2025/11/19/nvidia-nvda-earnings-report-q3-2026.html) | "
                    "[Fed Watch Tool](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) | "
                    "[BTC Analysis](https://www.fxstreet.com/cryptocurrencies/news)"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "⚡ BOTTOM LINE: $90,800 is the last defense before $88k. Mixed data = mixed sentiment. Best play: Long $90.5k-$91k with tight stops. Monitor volume and manage risk carefully. DYOR | NFA 🚀"
        }
    }

    # Discord webhook payload
    payload = {
        "content": "@everyone",
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ BTC Post-NFP & NVIDIA update sent successfully!")
            return True
        else:
            print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Discord message: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Sending BTC Post-NFP & NVIDIA Update to Discord...")
    print("=" * 60)

    success = send_btc_post_nfp_nvidia()

    if success:
        print("=" * 60)
        print("✅ BTC update delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
