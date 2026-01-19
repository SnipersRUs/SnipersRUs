#!/usr/bin/env python3
"""Send reset notification to Discord"""
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr"

embed = {
    "title": "♻️ Bounty Seeker Bot - Reset & Fresh Start",
    "color": 0x00FF00,
    "fields": [
        {
            "name": "📊 Account Reset",
            "value": "✅ All trades cleared\n✅ Starting balance: $1,000\n✅ 0 wins, 0 losses\n✅ Fresh start!",
            "inline": False
        },
        {
            "name": "🎯 New Selective Approach",
            "value": (
                "**Higher Quality Threshold:**\n"
                "• Confluence score: 65/100 minimum (was 55)\n"
                "• More selective - quality over quantity\n"
                "• Let trades come to you, don't rush\n"
                "• Only best setups will trigger\n\n"
                "**Patience is Key:**\n"
                "• Bot will wait for high-quality setups\n"
                "• Better confluence = better trades\n"
                "• No FOMO - only A+ opportunities"
            ),
            "inline": False
        },
        {
            "name": "⏰ What to Expect",
            "value": (
                "• Fewer signals (but higher quality)\n"
                "• Bot scans every 60 minutes\n"
                "• Only enters when confluence ≥ 65/100\n"
                "• Max 3 signals per hour\n"
                "• Max 3 open trades at once"
            ),
            "inline": False
        }
    ],
    "footer": {
        "text": "Bounty Seeker Bot • Quality Over Quantity • Patience Pays"
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}

try:
    payload = {"embeds": [embed]}
    r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
    r.raise_for_status()
    print("✅ Reset notification sent to Discord!")
except Exception as e:
    print(f"❌ Failed to send notification: {e}")








