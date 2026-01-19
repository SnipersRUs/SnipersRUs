#!/usr/bin/env python3
"""One-time Discord webhook test ping"""

import requests
import pytz
from datetime import datetime

TZ_NY = pytz.timezone("America/New_York")

WEBHOOK_URL = "https://discord.com/api/webhooks/1419912201124188161/u37vKgzcIff1nXnSk0NAaxlePMx6gRNYnlRHukdy6MmKDd3SZo_AZoAPtFqhclt8lJCB"

def ping_discord():
    """Send one-time ping to Discord"""
    embed = {
        "title": "✅ Macro Hunter Bot - Webhook Test",
        "description": "One-time ping to verify webhook connection",
        "color": 0x00bfff,
        "fields": [
            {
                "name": "🔗 Webhook Status",
                "value": "✅ Active & Working",
                "inline": True
            },
            {
                "name": "📊 Bot Status",
                "value": "Ready to Scan",
                "inline": True
            },
            {
                "name": "⏰ Test Time (ET)",
                "value": datetime.now(TZ_NY).strftime("%Y-%m-%d %H:%M:%S"),
                "inline": False
            }
        ],
        "footer": {
            "text": "MCRO Scanner • Webhook Verification"
        },
        "timestamp": datetime.now(TZ_NY).isoformat()
    }

    try:
        response = requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
        if response.status_code in (200, 201, 204):
            print("✅ SUCCESS: Webhook ping sent successfully!")
            print(f"   Response: {response.status_code}")
            return True
        else:
            print(f"❌ ERROR: Webhook returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Failed to send webhook ping")
        print(f"   Exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Discord Webhook Connection...")
    print(f"📡 Webhook URL: {WEBHOOK_URL[:50]}...")
    print("-" * 50)
    ping_discord()
    print("-" * 50)
    print("✅ Test complete!")








