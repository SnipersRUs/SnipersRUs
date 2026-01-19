#!/usr/bin/env python3
"""Send trade tracking improvements announcement"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

def send_update():
    embed = {
        "title": "🔧 Trade Tracking System Improved",
        "description": "**Better trade management and alerting system**",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "✅ What Changed",
                "value": "• **Trade numbering** - Each trade gets a unique number (#1, #2, etc.)\n• **Reset all stats** - Fresh start with clean P&L and W/L tracking\n• **Clear entry alerts** - Green alerts when trades are triggered\n• **Grouped notifications** - Multiple signals on same ticker = one card\n• **Better tracking** - Know exactly which trade is which",
                "inline": False
            },
            {
                "name": "🚨 Trade Entry Alerts",
                "value": "• **Green alert** when trade entry is triggered\n• Shows **Trade #X** prominently\n• Clear indication of which trade is being executed\n• All trade details in one place",
                "inline": False
            },
            {
                "name": "📊 Grouped Notifications",
                "value": "• Multiple signals on same ticker = **one card**\n• All signals grouped together\n• No more notification spam\n• Cleaner Discord feed",
                "inline": False
            },
            {
                "name": "🔢 Trade Numbering",
                "value": "• Starting from Trade #1\n• Sequential numbering for all trades\n• Track which trades work and which don't\n• Easy to reference specific trades",
                "inline": False
            },
            {
                "name": "📈 Tracking",
                "value": "• Reset P&L and W/L stats\n• Fresh start for tracking\n• Know what's valid and what's invalid\n• Learn which trades to take",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Improved Trade Tracking"
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

