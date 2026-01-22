#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Weekly Outlook
Sends BTC weekly analysis as a purple embed card to Discord
"""

import requests
import sys

def send_btc_weekly_outlook():
    """Send the BTC weekly outlook to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = ""

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "🔴 BTC WEEKLY OUTLOOK - NOV 18-22, 2025 🔴",
        "description": "**Current Price:** ~$94,908 | Down from $107k high",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "📊 CRITICAL LEVELS",
                "value": (
                    "🔴 **Resistance:** $95,500 | $96,500 | $98,000 | $100,000\n"
                    "🟢 **Support:** $93,150 | $91,800 | $90,000 | $88,000\n\n"
                    "⚠️ **KEY LEVEL: $93,150 - CHANNEL SUPPORT**\n"
                    "Breaking below = RIP to $85k-$90k zone"
                ),
                "inline": False
            },
            {
                "name": "🟢 LONG #1: Channel Support (70% win rate)",
                "value": (
                    "📍 Entry: $93,000-$93,500 (LADDER IN)\n"
                    "🛑 Stop: $91,800\n"
                    "🎯 Targets: $95.5k / $97.5k / $100k\n"
                    "💡 Best R/R of the week"
                ),
                "inline": False
            },
            {
                "name": "🟢 LONG #2: Breakout Play (55% win rate)",
                "value": (
                    "📍 Entry: $96,500 (break & retest)\n"
                    "🛑 Stop: $95,200\n"
                    "🎯 Targets: $98.5k / $100.5k / $103k"
                ),
                "inline": False
            },
            {
                "name": "🔴 SHORT #1: Lower High Rejection (60% win rate)",
                "value": (
                    "📍 Entry: $95,800-$96,200\n"
                    "🛑 Stop: $97,000\n"
                    "🎯 Targets: $94.5k / $93k / $91.5k\n"
                    "⚠️ Only if we pump into resistance"
                ),
                "inline": False
            },
            {
                "name": "🔴 SHORT #2: Channel Break (45% - HIGH RISK)",
                "value": (
                    "📍 Entry: $92,800 (below $93k)\n"
                    "🛑 Stop: $94,200\n"
                    "🎯 Targets: $90.5k / $88k / $85k\n"
                    "⚠️ Small size only - could be fakeout"
                ),
                "inline": False
            },
            {
                "name": "📅 THIS WEEK'S EVENTS",
                "value": (
                    "**MON NOV 18:** Markets digest weekend dump | Low volume\n"
                    "**TUE NOV 19:** Fed Beige Book (2PM EST)\n"
                    "**WED NOV 20:** 🚨 **SEPTEMBER JOBS REPORT (8:30AM EST)** - MAJOR VOLATILITY\n"
                    "**THU NOV 21:** THANKSGIVING - US markets CLOSED\n"
                    "**FRI NOV 22:** Black Friday - Half day (close 1PM EST)"
                ),
                "inline": False
            },
            {
                "name": "🌍 SESSION STRATEGIES",
                "value": (
                    "**ASIAN:** Gap down to $93k (40%) | Gap up to $95k (30%) | Range (30%)\n"
                    "**LONDON:** PRIME TRADING WINDOW - Long $93k (40%) | Short $95.5k (35%) | Range (25%)\n"
                    "**NEW YORK:** First 30min sets tone | Best trades: 9:30AM-11AM window"
                ),
                "inline": False
            },
            {
                "name": "⚠️ BEARISH CATALYSTS",
                "value": (
                    "• BTC down 9% worst week since March\n"
                    "• Fear & Greed: EXTREME FEAR (10/100)\n"
                    "• Open interest dropped $94B → $68B\n"
                    "• ETF inflows only $1M (very weak)\n"
                    "• Channel support at $93k CRITICAL"
                ),
                "inline": False
            },
            {
                "name": "✅ BULLISH CATALYSTS",
                "value": (
                    "• Historical Nov avg +42% since 2013\n"
                    "• Analysts target $114k end of Nov\n"
                    "• Fed rate cuts expected December\n"
                    "• Extremely oversold (RSI <30)\n"
                    "• $93k = major accumulation zone"
                ),
                "inline": False
            },
            {
                "name": "🎲 WEEKLY PROBABILITIES",
                "value": (
                    "**Next 48h:** 50% Chop $93k-$96k | 30% Bounce | 20% Dump\n"
                    "**After Jobs Report:** 40% Dump | 35% Rally | 25% Chop\n"
                    "**End of Week:** 45% Range | 30% Relief rally | 25% Breakdown\n\n"
                    "**Directional Bias:** Short-term Bearish-Neutral (35/65)"
                ),
                "inline": False
            },
            {
                "name": "💡 PRO TIPS",
                "value": (
                    "✅ **DO:** Ladder into longs at $93k-$95k | Use tight stops | Scale out profits\n"
                    "❌ **DON'T:** Chase pumps above $96k | Short absolute lows | FOMO into wicks\n"
                    "⚠️ **WATCH:** $93k breakdown = RIP to $85k-$90k"
                ),
                "inline": False
            },
            {
                "name": "🔗 KEY LINKS",
                "value": (
                    "[Fed Calendar](https://www.federalreserve.gov/newsevents/calendar.htm) | "
                    "[Economic Data](https://fred.stlouisfed.org/releases/calendar) | "
                    "[Jobs Report Info](https://www.cnbc.com/2025/11/14/heres-where-things-stand-on-when-the-government-will-start-releasing-key-economic-reports.html) | "
                    "[Market News](https://www.coindesk.com/)"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "⚡ BOTTOM LINE: $93k MUST hold or we're going to $85k-$90k. Wed jobs report is THE catalyst. DYOR | NFA | Manage risk fam! 🚀💎🙌"
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
            print("✅ BTC Weekly Outlook sent successfully!")
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
    print("🚀 Sending BTC Weekly Outlook to Discord...")
    print("=" * 60)

    success = send_btc_weekly_outlook()

    if success:
        print("=" * 60)
        print("✅ BTC Weekly Outlook delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

