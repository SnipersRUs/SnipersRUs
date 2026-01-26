#!/usr/bin/env python3
"""Send paper trading announcement"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = ""

def send_announcement():
    embed = {
        "title": "💰 Paper Trading Added to Cloudflare Bot",
        "description": "**Bot now executes paper trades automatically**",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "✅ What Was Added",
                "value": "• Paper trading system\n• Automatic trade execution\n• Position tracking\n• Trade execution alerts\n• Stop loss & take profit monitoring",
                "inline": False
            },
            {
                "name": "💰 Account Settings",
                "value": "• Starting Balance: **$1,000.00**\n• Trade Size: **$150.00** per trade\n• Max Open Trades: **3**\n• Leverage: **15x** (BTC: **25x**)",
                "inline": False
            },
            {
                "name": "📊 Trade Management",
                "value": "• Stop Loss: 2%\n• Take Profit: 3%\n• Automatic position monitoring\n• Real-time P&L tracking\n• W/L ratio tracking",
                "inline": False
            },
            {
                "name": "🔔 Alerts",
                "value": "You will receive alerts for:\n• Trade entries (white)\n• Trade exits (white for TP, red for stop)\n• Position updates\n• Account balance changes",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Paper Trading Active"
        }
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Announcement sent!")
            return True
        else:
            print(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_announcement()

