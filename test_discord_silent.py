#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Discord notifications without spam
"""

import requests
from datetime import datetime, timezone

def test_discord_notification():
    """Test Discord notification without spam"""
    webhook_url = "https://discord.com/api/webhooks/1430429617696673852/UmIz28ug7uMqCyuVyOy7LeGXRj91sGLM9NuZicfzSZQOvYlGdfulww0WZzqRLos2I6Jz"

    try:
        embed = {
            "title": "🧪 DISCORD TEST - NO SPAM",
            "description": "**Testing Discord notifications**\n"
                         "**Status:** ✅ Working\n"
                         "**Spam:** ❌ Disabled\n"
                         "**Bot:** Ready for trading",
            "color": 0x00FF00,
            "footer": {"text": f"Test • {datetime.now(timezone.utc).strftime('%H:%M UTC')}"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        payload = {"embeds": [embed]}
        response = requests.post(webhook_url, json=payload, timeout=10)
        print(f"📤 Discord test sent: {response.status_code}")

        if response.status_code == 204:
            print("✅ Discord notifications working!")
            return True
        else:
            print(f"❌ Discord test failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Discord test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Discord notifications...")
    test_discord_notification()















