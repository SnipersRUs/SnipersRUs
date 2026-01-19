#!/usr/bin/env python3
"""
Send Discord update about Forex Bot enhancements
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451483953897668610/uhi0EVl81jV4B17m6tbiwZ3fOV88F7goMERBn4Vyim4_owOpDNZK1regFliw4bcl8mBF"

def send_bot_update():
    """Send bot update announcement to Discord"""

    embed = {
        "title": "🚀 FOREX BOT UPDATED - FX-OPTIMIZED FEATURES",
        "description": (
            "**The bot has been upgraded with comprehensive FX-specific features!**\n\n"
            "**🎯 What's New:**\n\n"
        ),
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "✅ Session-Based VWAP",
                "value": (
                    "• London Session (08:00-17:00 UTC)\n"
                    "• New York Session (13:00-22:00 UTC)\n"
                    "• Tokyo Session (00:00-09:00 UTC)\n"
                    "• **London/NY Overlap** (13:00-17:00 UTC) - Best liquidity\n\n"
                    "Forex respects session boundaries more than daily levels!"
                ),
                "inline": False
            },
            {
                "name": "💰 Pip-Based Position Sizing",
                "value": (
                    "• Calculates lot sizes based on pip risk\n"
                    "• Formula: (Risk Amount ÷ Stop Loss in Pips) ÷ Pip Value\n"
                    "• 2% risk per trade\n"
                    "• Automatic pip detection (XXX/USD vs XXX/JPY)"
                ),
                "inline": True
            },
            {
                "name": "🛡️ Risk Management",
                "value": (
                    "• **Spread Filter**: Skips trades if spread > 2 pips\n"
                    "• **News Filter**: Avoids high-impact events (ready for API)\n"
                    "• **Market Hours**: Only trades 24/5 (closed weekends)\n"
                    "• **ATR Multipliers**: Optimized for forex (lower volatility)"
                ),
                "inline": True
            },
            {
                "name": "📊 Enhanced Signal Criteria",
                "value": (
                    "**A+ Setups Require:**\n"
                    "✅ Session VWAP deviation (2σ/3σ)\n"
                    "✅ Golden Pocket + Psychological level\n"
                    "✅ Pivot reversal on 15m+\n"
                    "✅ Spread ≤ 2 pips\n"
                    "✅ No news events\n"
                    "✅ Volume confirmation"
                ),
                "inline": False
            },
            {
                "name": "🔔 Discord Alerts",
                "value": (
                    "• **Premarket Updates**: Daily & Weekly\n"
                    "• **Pip-Based Metrics**: All alerts show pips\n"
                    "• **Session Info**: Current session in alerts\n"
                    "• **GP Proximity**: Distance in pips\n"
                    "• **A+ Setups**: Full trade details with R/R ratios"
                ),
                "inline": True
            },
            {
                "name": "⏰ Trading Hours",
                "value": (
                    "• **24/5 Operation**: Closed weekends\n"
                    "• **Auto-Detection**: Skips scans when market closed\n"
                    "• **Session Priority**: Overlap > London > NY > Tokyo\n"
                    "• **Premarket Updates**: Start of day/week"
                ),
                "inline": True
            },
            {
                "name": "📈 Forex-Optimized Settings",
                "value": (
                    "• **Leverage**: 100x (reduced from 150x)\n"
                    "• **Stop Loss**: 1.0x ATR (reduced for forex)\n"
                    "• **TP1**: 1.5x ATR (25% closes here)\n"
                    "• **TP2**: 2.5x ATR\n"
                    "• **TP3**: 4.0x ATR"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "Forex Pivot Reversal Bot • FX-Optimized • Ready for Trading"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        payload = {"embeds": [embed]}
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ Discord update sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send update: {e}")
        return False

if __name__ == "__main__":
    print("Sending Forex Bot update to Discord...")
    send_bot_update()







