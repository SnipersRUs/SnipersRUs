#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Weekly Plan
Sends Sniper Guru BTC weekly plan with @everyone ping to Discord channel
"""

import requests
import json
import sys
from datetime import datetime, timezone

def send_discord_message():
    """Send the BTC weekly plan to Discord with @everyone ping"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

    # Get current date/time
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%Y-%m-%d %H:%M UTC")

    # TradingView BTC link
    btc_tv_link = "https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT"

    # Create embed card
    embed = {
        "title": "🎯 SNIPER GURU – BTC WEEKLY PLAN (NY SESSION)",
        "url": btc_tv_link,
        "description": f"**Time:** {current_time}\n\n📌 **Context & Market Structure**",
        "color": 0xf7931a,  # Bitcoin orange color
        "fields": [
            {
                "name": "📊 Market Context",
                "value": """• Price recently pulled back into the ~105K range after a rally above ~103K. Momentum has slowed and liquidity zones are in focus.

• **Macro backdrop:**
  - The Federal Reserve (FOMC) calendar remains key for the USD, rates and risk sentiment.
  - Risk-off signals emerging: The "next year inflation expectations" ticked higher; consumer and services data point to mixed strength.

• **Crypto-specific:** BTC has broken back above ~103K and analysts see a chance of upside if liquidity and funding conditions align.""",
                "inline": False
            },
            {
                "name": "🎯 Bias & Probabilities (NY Session → Week)",
                "value": """• **Upside path (~50%):** If BTC holds above the session VWAP and shows strength through the ~106K zone, then upside toward ~108-110K is on the table.

• **Downside path (~40%):** If the price rejects the liquidity zone (~106K-107K) and loses the session VWAP, then a drop toward ~102K-100K becomes likely.

• **Neutral / range (~10%):** If price remains stuck between session VWAP and the liquidity zone without conviction, expect chop and mean-reversion.""",
                "inline": False
            },
            {
                "name": "🔍 Key Zones to Watch",
                "value": """• **Resistance / Liquidity Street:** ~106K-107K (important recent highs)
• **Control / Pivot:** Session VWAP (monitor real-time) around current price
• **Support / Shelf:** ~102K, then ~100K if sellers accelerate""",
                "inline": False
            },
            {
                "name": "🧭 NY Session Playbook",
                "value": """• **Long Trigger:** Price closes above the session VWAP + a 15-minute candle or spike that breaks ~106K-107K with volume. Target ~108-110K+. Invalidation = sustained close below VWAP with strong sell volume.

• **Short Trigger:** Price fails at the ~106K-107K zone (rejection with lower wick, close below the VWAP) → price loses session VWAP → target ~102K-100K. Invalidation = close back above VWAP and reclaim of the zone.

• **Risk Manage:** Into major macro prints (rate/CPI/data) reduce size or wait for post-print confirmation.""",
                "inline": False
            },
            {
                "name": "📎 News to Watch This Week",
                "value": """• Watch for upcoming major economic data releases and Fed statements.
• Crypto-flow highlight: Analysts note BTC may surge if liquidity loosens and USD strength stalls.""",
                "inline": False
            },
            {
                "name": "✅ Bottom Line",
                "value": """This week is about **liquidity & VWAP structure**.

Trade the reaction at the session VWAP and the ~106K-107K zone. Upside if we break & hold, downside if we reject and lose control. Macro prints = wild card.

Let's stay sharp. 🎯""",
                "inline": False
            },
            {
                "name": "📈 Chart Links",
                "value": f"[**BTC/USDT Chart (TradingView)**]({btc_tv_link})",
                "inline": False
            }
        ],
        "footer": {
            "text": "Sniper Guru • BTC Weekly Plan • Educational purposes only"
        },
        "timestamp": now.isoformat()
    }

    # Discord webhook payload with @everyone ping
    payload = {
        "content": "@everyone",
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=15)

        if response.status_code in [200, 204]:
            print("✅ Discord message sent successfully!")
            print(f"📊 Sent BTC Weekly Plan with @everyone ping")
            return True
        else:
            print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Discord message: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Sending BTC Weekly Plan to Discord...")
    print("=" * 50)

    success = send_discord_message()

    if success:
        print("=" * 50)
        print("✅ Mission accomplished! Check your Discord channel.")
    else:
        print("=" * 50)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)




