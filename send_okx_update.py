#!/usr/bin/env python3
"""Send OKX update announcement"""

import requests
from datetime import datetime, timezone

DISCORD_WEBHOOK = ""

def send_update():
    embed = {
        "title": "🔄 Exchange Updated to OKX",
        "description": "**Bot now uses OKX for market data and TradingView links**",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "✅ What Changed",
                "value": "• Primary exchange: **OKX** (perpetual futures)\n• TradingView links: **OKX perpetuals**\n• Fallback exchanges: Binance, Coinbase\n• All market data from OKX",
                "inline": False
            },
            {
                "name": "📊 TradingView Links",
                "value": "• BTC: `OKX:BTCUSDTPERP`\n• SOL: `OKX:SOLUSDTPERP`\n• ETH: `OKX:ETHUSDTPERP`",
                "inline": False
            },
            {
                "name": "⚡ Benefits",
                "value": "• More accurate perpetual futures data\n• Better liquidity tracking\n• Consistent exchange across all features",
                "inline": False
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": "Cloudflare Indicator Bot • OKX Integration"
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

