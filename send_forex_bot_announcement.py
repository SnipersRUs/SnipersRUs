#!/usr/bin/env python3
"""
Send Discord announcement about Forex Pivot Reversal Bot
"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451483953897668610/uhi0EVl81jV4B17m6tbiwZ3fOV88F7goMERBn4Vyim4_owOpDNZK1regFliw4bcl8mBF"

def send_announcement():
    """Send bot announcement to Discord"""

    embed = {
        "title": "🚀 FOREX PIVOT REVERSAL BOT - NOW LIVE",
        "description": (
            "**A specialized forex trading bot focused on pivots and reversals**\n\n"
            "This bot uses **three powerful indicators** to find the best entry points:\n\n"
            "**1️⃣ PivotX Pro** - Dynamic pivot detection\n"
            "   • ATR-based pivot strength (15+ pivots are stronger)\n"
            "   • Higher timeframes = stronger signals\n"
            "   • Detects exhaustion signals (selling/buying exhaustion)\n"
            "   • Volume spike confirmation required\n\n"
            "**2️⃣ Golden Pocket Syndicate (GPS)** - Golden pocket zones\n"
            "   • Tracks 0.618 and 0.65 Fibonacci levels\n"
            "   • Alerts when price approaches GP zones\n"
            "   • High-probability reversal areas\n\n"
            "**3️⃣ Tactical Deviation** - VWAP deviation bands\n"
            "   • Daily VWAP with ±1σ, ±2σ, ±3σ bands\n"
            "   • ±2σ = A- setup (good reversal)\n"
            "   • ±3σ = A+ setup (extreme reversal)\n"
            "   • Volume-backed signals only\n\n"
        ),
        "color": 0x00FF00,  # Green
        "fields": [
            {
                "name": "📊 What The Bot Is Looking For",
                "value": (
                    "✅ **Strong pivots** on 15m+ timeframes\n"
                    "✅ **Price near Golden Pocket zones** (0.618/0.65)\n"
                    "✅ **Extreme deviations** from VWAP (±2σ or ±3σ)\n"
                    "✅ **Exhaustion signals** (selling/buying exhaustion)\n"
                    "✅ **Volume confirmation** (1.5x average volume)\n"
                    "✅ **Pivot reversals** at key levels\n\n"
                    "**Signal Grades:**\n"
                    "• **A+ Setups**: 15m+ with strong confluence (auto-traded)\n"
                    "• **A- Setups**: 5m or ±2σ deviations (alerts only)"
                ),
                "inline": False
            },
            {
                "name": "💱 Trading Pairs",
                "value": (
                    "🇺🇸🇯🇵 **USD/JPY**\n"
                    "🇪🇺🇺🇸 **EUR/USD**\n"
                    "🇬🇧🇺🇸 **GBP/USD**\n\n"
                    "Focusing on these 3 major pairs for quality signals"
                ),
                "inline": True
            },
            {
                "name": "💰 Paper Trading Setup",
                "value": (
                    "**Starting Balance:** $1,000\n"
                    "**Leverage:** 150x\n"
                    "**Trade Size:** $50 per trade\n"
                    "**Max Positions:** 3 open at once\n"
                    "**TP Management:** 25% at TP1, rest at TP2/TP3"
                ),
                "inline": True
            },
            {
                "name": "🔔 Alert Types",
                "value": (
                    "**1. Golden Pocket Proximity** 🎯\n"
                    "   Shows distance to approaching GP zones\n\n"
                    "**2. A- Deviation Setups** 📊\n"
                    "   Purple = Bearish (SHORT)\n"
                    "   Green = Bullish (LONG)\n\n"
                    "**3. A+ Setups** ⭐\n"
                    "   Purple = Bearish (SHORT)\n"
                    "   Green = Bullish (LONG)\n"
                    "   Includes full trade details"
                ),
                "inline": False
            },
            {
                "name": "⚙️ How It Works",
                "value": (
                    "1. **Scans** all 3 pairs every 45 minutes\n"
                    "2. **Detects** pivots, GP proximity, and deviations\n"
                    "3. **Grades** signals (A+ or A-)\n"
                    "4. **Alerts** Discord for all setups\n"
                    "5. **Auto-trades** A+ setups (up to 3 positions)\n"
                    "6. **Manages** positions with TP/SL\n\n"
                    "**Risk Management:**\n"
                    "• Stop Loss: 1.5x ATR\n"
                    "• TP1: 2.5x ATR (25% closes here)\n"
                    "• TP2: 4.0x ATR\n"
                    "• TP3: 6.0x ATR"
                ),
                "inline": False
            }
        ],
        "footer": {
            "text": "Forex Pivot Reversal Bot • Focused on Quality Setups"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        payload = {"embeds": [embed]}
        response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ Discord announcement sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send announcement: {e}")
        return False

if __name__ == "__main__":
    print("Sending Forex Bot announcement to Discord...")
    send_announcement()







