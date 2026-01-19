#!/usr/bin/env python3
"""
Send RAY Short Trade details to Discord webhook
"""

import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

MESSAGE = """@everyone 🎯 **RAY SHORT TRADE** 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **TRADE DETAILS**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Pair:** RAY/USDT Perpetual (KCEX)

**Direction:** 🔴 SHORT

**Entry:** ~1.1491

**Quantity:** 3,521.127 RAY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **TARGETS & STOPS**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Take Profit:** 1.1043
**TP Distance:** -4.29% (0.0495)
**TP Amount:** 274.3 USDT

**Stop Loss:** 1.1538
**SL Distance:** +0.615% (0.0071)
**SL Amount:** 75 USDT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **RISK/REWARD**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Risk/Reward Ratio:** 6.97:1

**Current P&L:** +0.0047 USDT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **TRADE SETUP**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Shorting RAY at resistance with tight stop above. Targeting support zone at 1.1043 for 4.29% move.

Risk management: Tight stop at 0.615% with 6.97:1 R/R ratio.

Chart posted below 👇

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DYOR | NFA | Trade safe! ⚠️🎯"""

def send_to_discord():
    """Send RAY short trade to Discord"""
    payload = {
        "content": MESSAGE,
        "username": "Sniper Guru"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("✅ RAY Short Trade sent successfully to Discord!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to Discord: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    send_to_discord()








