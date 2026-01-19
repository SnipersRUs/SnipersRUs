#!/usr/bin/env python3
"""
Send RAY Short Trade in card format to Discord webhook
"""

import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

MESSAGE = """@everyone 🎯 **Trade ENTERED: RAY/USDT** 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Signal Details**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Setup Grade:** A
**Signal Type:** REVERSAL_BEAR
**Direction:** 🔴 SHORT
**Confidence:** High

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Why This Trade Was Signaled**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Reversal Bear - Price rejection at resistance with volume

✅ Multiple confluence levels detected

• Resistance rejection at 1.155 zone
• Volume confirmation on rejection
• Lower timeframe bearish structure
• Risk/Reward setup favorable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **Trade Parameters**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Entry Price:** $1.1550

**Stop Loss:** $1.1650 (0.87%)

**Invalidation:** Above $1.1650 (break of resistance)

**Take Profit 1:** $1.1043 (4.39%)

**Take Profit 2:** $1.0950 (5.19%)

**Risk/Reward:** 5.04:1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **Important Warning**

Always check the chart and use your own analysis!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Status:** ACTIVE

**Cloudfare Bot • Educational purposes only • NFA • DYOR**"""

def send_to_discord():
    """Send RAY short trade card to Discord"""
    payload = {
        "content": MESSAGE,
        "username": "Sniper Guru"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ RAY Short Trade Card sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_discord()
















