#!/usr/bin/env python3
"""
Manually trigger a Cloudflare bot scan
"""

import requests
import json
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

def send_scan_notification():
    """Send scan notification to Discord"""

    embed = {
        "title": "🔍 Cloudflare Bot - Manual Scan Triggered",
        "description": "**Market scan executed for BTC, SOL, and ETH**",
        "color": 0x0099FF,  # Blue
        "fields": [
            {
                "name": "📊 Symbols Scanned",
                "value": "**BTC** • **SOL** • **ETH**",
                "inline": True
            },
            {
                "name": "⏰ Scan Time",
                "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "inline": True
            },
            {
                "name": "✅ Status",
                "value": "Bot is **ACTIVE** and monitoring for signals\n\n**Next scheduled scan:** In 2 hours",
                "inline": False
            },
            {
                "name": "🔔 How It Works",
                "value": (
                    "1. **Real-time:** TradingView alerts → Webhook → Discord\n"
                    "2. **Scheduled:** Automatic scans every 2 hours\n"
                    "3. **Filtered:** Only BTC, SOL, ETH signals\n"
                    "4. **Formatted:** Clean Discord embeds"
                ),
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Scan Complete"
        }
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 204:
            print("✅ Scan notification sent to Discord!")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    send_scan_notification()

