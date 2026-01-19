#!/usr/bin/env python3
"""
Send PivotX Pro update announcement to Discord
"""

import requests
from datetime import datetime, timezone

WEBHOOK_URL = "https://discord.com/api/webhooks/1363315528831340787/KfoIJA6G1eEYjegzgrkgZ2qtDaaHL1hrs-ocU00wajpAdNsejWOm5HTvsmCYyrF9jOgr"
TV_LINK = "https://www.tradingview.com/script/BQXcICYn-PivotX/"

def create_pivotx_embed():
    """Create purple Discord embed card for PivotX Pro update"""

    embed = {
        "title": "🚀 PivotX Pro v2.0 - Major Update!",
        "description": (
            "**Complete Market Structure Analysis Tool**\n\n"
            "## ✨ What's New\n\n"
            "**🎯 Core Enhancements:**\n"
            "• Dynamic ATR-Based Pivot Detection\n"
            "• Market Structure Shift (CHoCH) Detection\n"
            "• Pivot Zone Visualization\n"
            "• Auto-Draw Fibonacci Retracements\n"
            "• Golden Pocket Highlighting (0.618)\n"
            "• Multi-Timeframe Filtering\n"
            "• ATR Confirmation System\n"
            "• Enhanced Alert System (6+ types)\n\n"
            "**🔧 Technical Improvements:**\n"
            "• Optimized for 3m+ charts (1m disabled)\n"
            "• Performance optimized\n"
            "• Smart error handling\n"
            "• Clean code architecture\n\n"
            "**🔄 Major Changes:**\n"
            "✅ Market structure tracking & CHoCH detection\n"
            "✅ Pivot zone boxes with labels\n"
            "✅ Fibonacci retracement tool\n"
            "✅ Multi-timeframe filtering\n"
            "✅ ATR confirmation system\n"
            "✅ Enhanced alert system (6+ types)\n"
            "✅ Dynamic pivot strength calculation\n"
            "✅ Golden Pocket highlighting\n\n"
            f"**[📊 View on TradingView]({TV_LINK})**"
        ),
        "color": 0x9B59B6,  # Purple color
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "PivotX Pro • Complete Market Structure Analysis"
        },
        "url": TV_LINK
    }

    return embed

def send_to_discord():
    """Send the update announcement to Discord"""

    embed = create_pivotx_embed()

    payload = {
        "embeds": [embed],
        "username": "PivotX Pro"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=15)
        response.raise_for_status()
        print("✅ PivotX Pro update sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_discord()




