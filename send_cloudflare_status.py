#!/usr/bin/env python3
"""
Send Cloudflare Bot status update
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = ""

def send_status():
    """Send bot status update"""

    embed = {
        "title": "✅ Cloudflare Bot - ONLINE & SCANNING",
        "description": "**Bot is now active and monitoring markets**",
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "🟢 Status",
                "value": "**ACTIVE**\nWebhook server running\nScheduled scans enabled",
                "inline": True
            },
            {
                "name": "📊 Current Activity",
                "value": "• Listening for TradingView webhooks\n• Scheduled scans every 2 hours\n• Monitoring BTC, SOL, ETH",
                "inline": True
            },
            {
                "name": "🔗 Webhook URL",
                "value": "`http://YOUR_SERVER:5000/webhook`\n*Configure this in TradingView alerts*",
                "inline": False
            },
            {
                "name": "📝 Next Steps",
                "value": (
                    "1. Add Cloudflare indicator to TradingView charts (BTC/SOL/ETH)\n"
                    "2. Create alerts for signal types you want\n"
                    "3. Set webhook URL in alert settings\n"
                    "4. Signals will appear here automatically!"
                ),
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Ready for signals"
        }
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Status update sent!")
            return True
        else:
            print(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_status()

