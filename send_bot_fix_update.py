#!/usr/bin/env python3
"""
Send update about bot fix
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

def send_update():
    """Send bot fix update"""

    embed = {
        "title": "🔧 Cloudflare Bot - Signal Detection FIXED",
        "description": "**Bot is now actively scanning and detecting signals**",
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "✅ What Was Fixed",
                "value": (
                    "• **Added real market data fetching** (Binance API)\n"
                    "• **Implemented Cloudflare signal detection**\n"
                    "• **Active scanning every 45 minutes**\n"
                    "• **Real-time signal alerts to Discord**"
                ),
                "inline": False
            },
            {
                "name": "📊 Signal Detection",
                "value": (
                    "**Detecting:**\n"
                    "• Bull/Bear Confirmations\n"
                    "• Golden Cross / Death Cross\n"
                    "• VWAP Breaks\n"
                    "• Divergence Signals\n"
                    "• Liquidity Flushes"
                ),
                "inline": True
            },
            {
                "name": "🎯 Symbols",
                "value": "**BTC** • **SOL** • **ETH**\n*Scanning every 45 min*",
                "inline": True
            },
            {
                "name": "ℹ️ Why No Signals?",
                "value": (
                    "If no signals detected, it means:\n"
                    "• Market conditions don't meet Cloudflare criteria\n"
                    "• Need multiple confirmations (trend + volume + price action)\n"
                    "• Signals require significant moves with volume\n\n"
                    "**The bot is working correctly** - it will alert when valid signals appear!"
                ),
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Now actively detecting signals"
        }
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Update sent!")
            return True
        else:
            print(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_update()

