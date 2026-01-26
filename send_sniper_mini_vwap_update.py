#!/usr/bin/env python3
"""
Send Sniper Mini VWAP [Real-Time Optimized] update announcement to Discord
"""

import requests
from datetime import datetime, timezone

WEBHOOK_URL = ""
TV_LINK = "https://www.tradingview.com/script/YOUR_SCRIPT_ID_HERE/"  # Update with actual TradingView link

def create_sniper_vwap_embed():
    """Create purple Discord embed card for Sniper Mini VWAP update"""

    embed = {
        "title": "🚀 Sniper Mini VWAP v2.0 - Real-Time Optimized Update!",
        "description": (
            "**Mean Reversion Trading with Multi-Timeframe VWAP**\n\n"
            "## ✨ What's New\n\n"
            "**🎯 Strategy Change: Breakout → Mean Reversion**\n"
            "• ✅ Buy signals at ORB **low support** (buying bottoms, not tops!)\n"
            "• ✅ Sell signals at ORB **high resistance** (selling tops, not bottoms!)\n"
            "• ✅ Mean reversion approach - buy support, sell resistance\n\n"
            "**🔧 Technical Improvements:**\n"
            "• ✅ **No Repainting:** VWAP uses `lookahead_off` for real-time reliability\n"
            "• ✅ **Cleaner Code:** User-defined types instead of multiple arrays\n"
            "• ✅ **Simplified ORB Bias:** Tight/wide detection based on ATR\n"
            "• ✅ **Better Signals:** Text labels (\"BUY\"/\"SELL\") instead of circles\n\n"
            "**⚙️ Default Settings:**\n"
            "• ✅ **ORB Disabled by Default** - Clean chart on load\n"
            "• ✅ **VWAP Only** - Focus on multi-timeframe analysis first\n"
            "• ✅ **Standard Colors** - Green (1H), Orange (4H), Purple (8H), Red (Daily)\n\n"
            "**🎨 Visual Enhancements:**\n"
            "• ✅ Cross-style VWAP lines (thin, clean)\n"
            "• ✅ Green/Red signal colors (more intuitive)\n"
            "• ✅ Simplified design (removed session-specific colors)\n\n"
            "**➕ New Features:**\n"
            "• ✅ **Trend Filter:** Optional filter aligning signals with daily trend\n"
            "• ✅ **ATR Touch Detection:** More accurate mean reversion timing\n"
            "• ✅ **No Volume Requirement:** Signals based on price action alone\n\n"
            "**🔄 Major Changes:**\n"
            "✅ Strategy: Breakout → Mean Reversion\n"
            "✅ ORB Default: On → Off (cleaner chart)\n"
            "✅ VWAP Repainting: Yes → No (real-time)\n"
            "✅ Signal Display: Circles → Text Labels\n"
            "✅ Code Structure: Arrays → User Types\n\n"
            f"**[📊 View on TradingView]({TV_LINK})**"
        ),
        "color": 0x9B59B6,  # Purple color
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Sniper Mini VWAP • Real-Time Optimized • Mean Reversion Trading"
        },
        "url": TV_LINK
    }

    return embed

def send_to_discord():
    """Send the update announcement to Discord"""

    embed = create_sniper_vwap_embed()

    payload = {
        "embeds": [embed],
        "username": "Sniper Mini VWAP"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ Sniper Mini VWAP update sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_discord()
