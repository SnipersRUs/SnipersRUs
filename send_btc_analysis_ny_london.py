#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Analysis - NY Close & London Session
Sends BTC analysis as a purple embed card to Discord
"""

import requests
import sys

def send_btc_analysis():
    """Send the BTC analysis to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = ""

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "🔴 BTC ANALYSIS - NY CLOSE & LONDON SESSION 🔴",
        "description": "**Current Price:** ~$100,046\n**BTC Dominance:** 60.15% (consolidating 59.8-60.4%)",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "📊 KEY LEVELS",
                "value": (
                    "**Resistance:** $100,850 | $102,000 | $103,500\n"
                    "**Support:** $98,500 | $97,200 | $96,000"
                ),
                "inline": False
            },
            {
                "name": "🎯 LONG SETUP 1: Demand Zone Long (65% win rate)",
                "value": (
                    "📍 Entry: $98,000-$98,500 (ladder in)\n"
                    "🛑 Stop: $97,200\n"
                    "🎯 Targets: $100k / $101.5k / $103k"
                ),
                "inline": False
            },
            {
                "name": "🎯 LONG SETUP 2: Breakout Long (55% win rate)",
                "value": (
                    "📍 Entry: $100,850 (break & retest)\n"
                    "🛑 Stop: $99,800\n"
                    "🎯 Targets: $102k / $103.5k / $105k"
                ),
                "inline": False
            },
            {
                "name": "📉 SHORT SETUP: Lower High Rejection (50% win rate)",
                "value": (
                    "📍 Entry: $101,000-$101,500\n"
                    "🛑 Stop: $102,200\n"
                    "🎯 Targets: $99.5k / $98k / $96.8k"
                ),
                "inline": False
            },
            {
                "name": "🌍 NY CLOSE (Next few hours)",
                "value": (
                    "• Below $100k close = bearish continuation\n"
                    "• Above $100k close = slight relief\n"
                    "• Avoid positions 30min before close"
                ),
                "inline": False
            },
            {
                "name": "🌍 LONDON (3AM EST/8AM GMT)",
                "value": (
                    "• Gap down to $97-98k → Long on hammer (40%)\n"
                    "• Range $98-100k → Scalp the range (45%)\n"
                    "• Gap up above $101k → Long pullback (15%)\n"
                    "• First hour 8-9am GMT = highest volatility"
                ),
                "inline": False
            },
            {
                "name": "⚠️ BEARISH CATALYSTS",
                "value": (
                    "• ETF outflows continue\n"
                    "• Institutional buying < daily mined BTC\n"
                    "• Fear & Greed: Extreme Fear (15-24)\n"
                    "• Macro uncertainty persists"
                ),
                "inline": False
            },
            {
                "name": "✅ BULLISH CATALYSTS",
                "value": (
                    "• MicroStrategy still buying (641k BTC stack)\n"
                    "• Oversold on lower timeframes\n"
                    "• Analysts target $114k+ end of Nov\n"
                    "• $100k psychological support"
                ),
                "inline": False
            },
            {
                "name": "🎲 PROBABILITIES (24h)",
                "value": (
                    "• 50% → Chop between $98k-$101k\n"
                    "• 30% → Relief bounce to $101.5k-$103k\n"
                    "• 20% → Breakdown to $96k-$97.5k\n\n"
                    "**Directional Bias:**\n"
                    "• Short-term: Slightly bearish (40/60)\n"
                    "• Medium-term: Neutral (50/50)\n"
                    "• End of Nov: Bullish (65%)"
                ),
                "inline": False
            },
            {
                "name": "⚡ RISK MANAGEMENT",
                "value": (
                    "• Market is choppy - reduce position sizes\n"
                    "• Honor your stops (volatility is high)\n"
                    "• Best R/R on dips to $98k zone\n"
                    "• Be patient for clear setups\n"
                    "• London first hour = prime time"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "DYOR | NFA | Trade safe fam! 🚀"
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
            print("✅ BTC Analysis sent successfully!")
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
    print("🚀 Sending BTC Analysis to Discord...")
    print("=" * 60)

    success = send_btc_analysis()

    if success:
        print("=" * 60)
        print("✅ BTC Analysis delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

