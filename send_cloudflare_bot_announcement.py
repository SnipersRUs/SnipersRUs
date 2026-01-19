#!/usr/bin/env python3
"""
Send Cloudflare Bot announcement to Discord
"""

import requests
import json
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

def send_bot_announcement():
    """Send announcement about Cloudflare Bot functionality"""

    embed = {
        "title": "🚀 Cloudflare Indicator Discord Bot - ACTIVE",
        "description": "**Real-time signal detection bot for BTC, SOL, and ETH**",
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "📊 Monitored Symbols",
                "value": "**BTC** • **SOL** • **ETH**\n*Only these symbols are processed*",
                "inline": True
            },
            {
                "name": "⏰ Scan Schedule",
                "value": "**Every 2 Hours**\nAutomatic market scanning",
                "inline": True
            },
            {
                "name": "🔔 Signal Types",
                "value": (
                    "🟢 **LONG Signals:**\n"
                    "• Master Long\n"
                    "• Bull Confirmation\n"
                    "• Bullish Divergence\n"
                    "• Golden Cross\n"
                    "• VWAP Break Above\n"
                    "• Liquidity Flush Bull\n\n"
                    "🔴 **SHORT Signals:**\n"
                    "• Master Short\n"
                    "• Bear Confirmation\n"
                    "• Bearish Divergence\n"
                    "• Death Cross\n"
                    "• VWAP Break Below\n"
                    "• Liquidity Flush Bear"
                ),
                "inline": False
            },
            {
                "name": "⚡ Real-Time Alerts",
                "value": (
                    "Receives **TradingView webhooks** instantly when signals trigger\n"
                    "Each signal = **single Discord card**\n"
                    "Multiple signals = **combined card**"
                ),
                "inline": False
            },
            {
                "name": "🎯 Focus",
                "value": (
                    "✅ **Long/Short signals only**\n"
                    "✅ **No paper trading** - signals only\n"
                    "✅ **BTC, SOL, ETH exclusive**\n"
                    "✅ **Optimized formatting**"
                ),
                "inline": False
            },
            {
                "name": "🌐 Webhook Endpoint",
                "value": "`http://YOUR_SERVER:5000/webhook`\n*Configure in TradingView alerts*",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Ready to receive signals"
        }
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 204:
            print("✅ Bot announcement sent to Discord!")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error sending announcement: {e}")
        return False

if __name__ == "__main__":
    send_bot_announcement()

