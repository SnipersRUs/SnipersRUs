#!/usr/bin/env python3
"""
Send update about scan interval change
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = ""

def send_update():
    """Send scan interval update"""

    embed = {
        "title": "⚙️ Cloudflare Bot - Scan Interval Updated",
        "description": "**Bot configuration updated**",
        "color": 0x0099FF,  # Blue
        "fields": [
            {
                "name": "⏰ New Scan Interval",
                "value": "**Every 45 minutes**\n*Previously: Every 2 hours*",
                "inline": True
            },
            {
                "name": "✅ Status",
                "value": "**ACTIVE**\nBot restarted with new settings",
                "inline": True
            },
            {
                "name": "📊 What This Means",
                "value": (
                    "• Market scans run **every 45 minutes**\n"
                    "• Scan notifications sent to Discord\n"
                    "• Real-time webhook alerts still active\n"
                    "• Next scan in ~45 minutes"
                ),
                "inline": False
            },
            {
                "name": "🔍 Scan Details",
                "value": (
                    "**Symbols:** BTC, SOL, ETH\n"
                    "**Frequency:** Every 45 minutes\n"
                    "**Notifications:** Enabled\n"
                    "**Webhook Alerts:** Real-time"
                ),
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Updated Configuration"
        }
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Update sent to Discord!")
            return True
        else:
            print(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_update()

