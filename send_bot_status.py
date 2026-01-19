#!/usr/bin/env python3
"""
Send bot status update to Discord
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451483953897668610/uhi0EVl81jV4B17m6tbiwZ3fOV88F7goMERBn4Vyim4_owOpDNZK1regFliw4bcl8mBF"

def send_status():
    """Send bot status update"""

    embed = {
        "title": "✅ FOREX BOT IS ACTIVE & RUNNING",
        "description": (
            "**Bot Status: 🟢 ONLINE**\n\n"
            "**Currently Scanning For:**\n\n"
            "**⚡ SCALPS (5m timeframe)**\n"
            "• Quick in/out trades\n"
            "• A- grade setups\n"
            "• ±2σ deviations\n"
            "• 5m pivot reversals\n\n"
            "**📈 SWINGS (15m+ timeframe)**\n"
            "• Higher timeframe moves\n"
            "• A+ grade setups\n"
            "• ±3σ deviations\n"
            "• Golden Pocket + Psychological levels\n"
            "• Strong confluence (3+ confirmations)\n\n"
        ),
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "🎯 Trading Pairs",
                "value": (
                    "• USD/JPY\n"
                    "• EUR/USD\n"
                    "• GBP/USD"
                ),
                "inline": True
            },
            {
                "name": "⏰ Scan Settings",
                "value": (
                    "• **Interval**: Every 45 minutes\n"
                    "• **Market Hours**: 24/5\n"
                    "• **Session**: Auto-detected\n"
                    "• **Max Positions**: 3"
                ),
                "inline": True
            },
            {
                "name": "🔍 Signal Detection",
                "value": (
                    "**Scalps (A-):**\n"
                    "✅ 5m pivots\n"
                    "✅ ±2σ deviations\n"
                    "✅ Volume confirmation\n\n"
                    "**Swings (A+):**\n"
                    "✅ 15m+ pivots\n"
                    "✅ ±3σ deviations\n"
                    "✅ Golden Pocket zones\n"
                    "✅ Psychological levels\n"
                    "✅ Exhaustion signals"
                ),
                "inline": False
            },
            {
                "name": "📊 Auto-Trading",
                "value": (
                    "• **A+ Swings**: Auto-traded (up to 3 positions)\n"
                    "• **A- Scalps**: Alerts only (manual review)\n"
                    "• **Risk**: 2% per trade\n"
                    "• **Leverage**: 100x"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "Forex Pivot Reversal Bot • Actively Hunting Scalps & Swings"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        payload = {"embeds": [embed]}
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ Status update sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send status: {e}")
        return False

if __name__ == "__main__":
    print("Sending bot status to Discord...")
    send_status()






