#!/usr/bin/env python3
"""
Send Bounty Seeker Bot announcement to Discord
"""
import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1432976746692612147/SLf6oNcxTZfnmt1LmGLv-asGHwi-BnR2T8XIneUr7zM1tTbsSMncMZgzytvTFiAHmpcr"

def send_announcement():
    """Send bot announcement and trade plan to Discord"""

    embed1 = {
        "title": "🎯 Bounty Seeker Bot - Live & Scanning",
        "description": "Reversal Trading Bot catching bottoms and tops using Elliott Wave 3 pullbacks",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "🤖 What The Bot Is Doing",
                "value": "Scanning MEXC Futures every 60 minutes\n• Filters: $500k+ 24h volume\n• Timeframes: 15m, 1h, 4h focus\n• Max 3 signals per hour\n• Paper trading: $1,000 balance\n• Max 3 open trades",
                "inline": False
            },
            {
                "name": "📊 Indicators Used",
                "value": "✅ GPS (Golden Pocket) - 0.618-0.65 zones\n✅ Oath Keeper - Macro divergences\n✅ SFP - 3-level confluence\n✅ Mini VWAPs - Trend analysis\n✅ Tactical Deviation - ±2σ/±3σ\n✅ Elliott Wave 3 - ABC pullbacks",
                "inline": False
            },
            {
                "name": "📊 Signal Types",
                "value": "🟢 Green = LONG signals\n🟣 Purple = SHORT signals\n⭐ Gold = A+ REVERSAL (±3σ)\n🟠 Orange = Watchlist (3 coins)\n🔔 Gold = SFP approaching (top 3)\n🚨 Blue = Trade entered",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    embed2 = {
        "title": "📈 Trade Plan - How To Use Signals",
        "color": 0x0099FF,
        "fields": [
            {
                "name": "Entry & Position Sizing",
                "value": "• Entry: Market price when signal generated\n• Size: $100 base @ 15x = $1,500 exposure\n• Max Risk: 3% stop loss per trade",
                "inline": False
            },
            {
                "name": "Take Profit & Stop Loss",
                "value": "• TP1: 1.75% - Take aggressively\n• TP2: 3% - If TP1 hits, can continue\n• Stop: 3% - Max loss per trade",
                "inline": False
            },
            {
                "name": "Risk Management Rules",
                "value": "• Max 3 trades open at once\n• No repeat entries on failed trades\n• Let winners run to TP2 if TP1 hits\n• Cut losses quickly at stop",
                "inline": False
            },
            {
                "name": "Signal Quality Guide",
                "value": "• A+ Reversals (±3σ): Highest quality\n• Plus Signals (±2σ): Good quality\n• Watchlist: Monitor for setups\n• SFP Approaching: Early warnings",
                "inline": False
            },
            {
                "name": "Best Practices",
                "value": "• Wait for price confirmation (don't FOMO)\n• Check higher timeframes for trend\n• Never risk more than 3% per trade\n• Set stop loss immediately\n• Take TP1 aggressively",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    embed3 = {
        "title": "⚠️ Important Disclaimers",
        "color": 0xFF0000,
        "fields": [
            {
                "name": "DYOR - Do Your Own Research",
                "value": "• Automated signals, NOT financial advice\n• Always verify on your charts\n• Check multiple timeframes\n• Understand the indicators",
                "inline": False
            },
            {
                "name": "Don't Blindly Follow Trades",
                "value": "• Signals are tools, not guarantees\n• Markets change rapidly\n• Past performance ≠ future results\n• Always use proper risk management",
                "inline": False
            },
            {
                "name": "NFA - Not Financial Advice",
                "value": "• Educational purposes only\n• Trading involves risk of loss\n• Only trade what you can afford to lose\n• Consult financial advisor if needed",
                "inline": False
            },
            {
                "name": "Paper Trading Mode",
                "value": "• Currently in paper trading mode\n• Starting balance: $1,000\n• All trades are simulated\n• Real trading requires additional setup",
                "inline": False
            }
        ],
        "footer": {
            "text": "Bounty Seeker Bot • Always DYOR • NFA • Trade Responsibly"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        payload = {"embeds": [embed1, embed2, embed3]}
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        r.raise_for_status()
        print("✅ Announcement sent to Discord successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send announcement: {e}")
        print(f"Response: {r.text if 'r' in locals() else 'No response'}")
        return False

if __name__ == "__main__":
    send_announcement()
