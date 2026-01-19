#!/usr/bin/env python3
"""Send accuracy improvements announcement"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1451743020188963060/d1jtofalj83RbUQVUOAPhws7rQfTJUzV8tf1AjXiAIWU6BoVoucV-UYfO2tDb7M_fzSS"

def send_update():
    embed = {
        "title": "🎯 Bot Accuracy Improvements - Fresh Start",
        "description": "**Stricter filters for fewer, more accurate trades**",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "✅ What Changed",
                "value": "• **Stricter signal filters** - Only high-quality signals\n• **Signal strength scoring** - Minimum 70/100 required\n• **Higher trend requirements** - Longs need score ≥7 (was 6), Shorts need ≤3 (was 4)\n• **Volume requirement** - Minimum 1.5x average volume (was 1.2x)\n• **MA crossover required** - Must have MA crossover confirmation\n• **RSI confirmation required** - RSI must align with direction\n• **Removed weak signals** - VWAP breaks removed, only strong divergences",
                "inline": False
            },
            {
                "name": "📊 Signal Quality Filters",
                "value": "• Minimum Signal Strength: **70/100**\n• Minimum Volume: **1.5x** average\n• Trend Score Long: **≥7** (was 6)\n• Trend Score Short: **≤3** (was 4)\n• MA Crossover: **Required**\n• RSI Confirmation: **Required**",
                "inline": False
            },
            {
                "name": "📈 Enhanced Tracking",
                "value": "• **All stats reset** - Fresh start from here\n• Win rate tracking\n• Average win/loss\n• Largest win/loss\n• Total P&L tracking\n• Complete trade history",
                "inline": False
            },
            {
                "name": "🎯 Expected Results",
                "value": "• **Fewer trades** - Only taking high-probability setups\n• **Higher accuracy** - Stricter filters = better win rate\n• **Better tracking** - Know exactly what's working\n• **Quality over quantity** - Every trade counts",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • Accuracy Focused"
        }
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]}, timeout=10)
        if response.status_code == 204:
            print("✅ Update sent!")
            return True
        else:
            print(f"Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    send_update()
