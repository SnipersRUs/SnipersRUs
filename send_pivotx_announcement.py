#!/usr/bin/env python3
"""
Discord Webhook Script for PivotX Indicator Announcement
Sends PivotX announcement as a purple sniper card to Discord
"""

import requests
import json
from datetime import datetime, timezone

def send_pivotx_announcement():
    """Send the PivotX announcement to Discord as a purple sniper card"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1363315528831340787/KfoIJA6G1eEYjegzgrkgZ2qtDaaHL1hrs-ocU00wajpAdNsejWOm5HTvsmCYyrF9jOgr"

    # Purple color for sniper card
    PURPLE_COLOR = 0x8E44AD

    # TradingView link
    tv_link = "https://www.tradingview.com/script/BQXcICYn-PivotX/"

    # Create the embed
    embed = {
        "title": "🎯 NEW INDICATOR: PivotX - Exhaustion & Pivot Detection 🎯",
        "description": f"**[{tv_link}]({tv_link})**\n\n*Your market exhaustion detector that spots when one side runs out of steam*",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "🔍 What PivotX Does",
                "value": (
                    "**🟢 Green X (Below Price):**\n"
                    "• Selling exhausted → Buyers stepping in\n"
                    "• Potential upward reversal signal\n\n"
                    "**🔴 Red X (Above Price):**\n"
                    "• Buying exhausted → Sellers stepping in\n"
                    "• Potential downward reversal signal\n\n"
                    "**💎 Yellow Diamonds:**\n"
                    "• Major pivot points (support/resistance)\n"
                    "• Key levels where price reversed\n\n"
                    "**📏 Neon Lines:**\n"
                    "• Support (green) & Resistance (red)\n"
                    "• Future key levels for trading"
                ),
                "inline": False
            },
            {
                "name": "⚡ Perfect For",
                "value": (
                    "✅ Swing trading reversals\n"
                    "✅ Identifying trend exhaustion\n"
                    "✅ Finding key support/resistance\n"
                    "✅ Counter-trend entries\n"
                    "✅ Scalping exhaustion points"
                ),
                "inline": True
            },
            {
                "name": "🔗 Pairs Great With",
                "value": (
                    "🎯 **Tactical Deviation**\n"
                    "• Combine exhaustion signals with deviation zones\n"
                    "• Higher probability setups when both align\n"
                    "• Perfect for scalping and swing trades"
                ),
                "inline": True
            },
            {
                "name": "📊 How It Works",
                "value": (
                    "PivotX uses **multi-signal confirmation**:\n"
                    "• Volume exhaustion patterns\n"
                    "• Price stabilization detection\n"
                    "• Absorption/distribution patterns\n"
                    "• Support/resistance confirmation\n\n"
                    "**Requires 3+ signals** for confirmation - reduces false signals!"
                ),
                "inline": False
            },
            {
                "name": "⚠️ Important Reminder",
                "value": (
                    "**Always DYOR!** 🔍\n\n"
                    "Indicators are **tools**, not guarantees.\n"
                    "**Market structure knowledge** is essential.\n"
                    "Combine with proper risk management.\n\n"
                    "*The best traders understand what signals mean and how to use them in their overall strategy.*"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "SnipersRUs • PivotX Indicator"
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "url": tv_link
    }

    # Discord webhook payload
    payload = {
        "embeds": [embed]
    }

    # Send to Discord
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print("✅ PivotX announcement sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending announcement: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_pivotx_announcement()



