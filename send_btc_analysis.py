#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Analysis
Sends Thursday London → NY game plan to Discord channel
"""

import requests
import json
import sys

def send_btc_analysis():
    """Send the BTC analysis to Discord"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

    # The BTC analysis message content (condensed to fit Discord 2000 char limit)
    message_content = """**THURSDAY LONDON → NY GAME PLAN — OCT 9, 2025**
**BTC | ETH | SOL**

**STATE**
Price ≈ 122.0–122.6k. After ATH, digesting under VWAP with lower highs on 15m/1h, while H4/D1 structure points up. Tape says "balanced-to-leaning-bid" if VWAP reclaimed.

**BIAS**
• Squeeze higher (stop early shorts): 50%
• Range-to-down continuation: 40%
• Full dump: 10%

**KEY LEVELS**
• R: 122.9k → 123.6k → 124.4k
• Pivot: 122.2k–122.4k (VWAP control)
• S: 121.6k–121.9k → 120.7k–120.1k
• Invalidate bull: <119.9k

**SCENARIOS**

**1) VWAP RECLAIM LONG**
• Trigger: 15m close >122.4k, retest holds
• Entry: 122.45k–122.55k | Stop: 121.95k
• Targets: 123.20k → 123.95k → 124.60k

**2) SWEEP-LIFT LONG**
• Trigger: Sweep 121.6k–121.9k, reclaim 122.0k
• Entry: 121.8k | Stop: 121.25k
• Targets: 122.8k → 123.5k → 124.2k

**3) FADE SHORT**
• Trigger: Reject 122.9k–123.6k + div
• Entry: 123.3k | Stop: 123.95k
• Targets: 122.4k → 121.9k → 120.9k

**4) BEAR CONTROL**
• Trigger: Accept <121.4k
• Entry: 121.25k | Stop: 121.85k
• Targets: 120.7k → 119.9k → 118.9k

**RISK**
• 0.5–1% per idea. 3-strike rule
• Partial +0.8R. Trail VWAP/swing
• CPI/PPI → flatten

**ETH & SOL**
• ETH: 3.45k reclaim → 3.55k/3.62k | S: 3.38k
• SOL: >195 bullish → 201/205 | <192 range

**CATALYSTS**
• Israel-Hamas ceasefire (risk-on)
• Ukraine strikes (mild risk-off)
• Oil stable post-OPEC+
• $5.95B crypto inflows (BTC-led)
• PPI/CPI next week (vol pockets)

**APPROACH**
• London sets VWAP bias, NY confirms/fades
• Best: VWAP reclaims + sweeps 121.6k–122.0k
• Avoid mid-range

**COMMUNITY**
Indicators: https://snipersrus.github.io/SnipersRUs/
@bountyseeker: $60/mo, 3-day trial

**BOTTOM LINE**
Controlled pullback post-ATH. VWAP >122.4k → squeeze 123.9k–124.6k. <121.4k → defense 120.7k. Patience first, precision second."""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://cdn.discordapp.com/attachments/1234567890/1234567890/sniper_guru_avatar.png"  # Optional: add avatar URL
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload)

        if response.status_code == 204:
            print("✅ Discord BTC analysis sent successfully!")
            print(f"📊 Message length: {len(message_content)} characters")
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
    print("📈 Sending BTC Analysis to Discord...")
    print("=" * 60)

    success = send_btc_analysis()

    if success:
        print("=" * 60)
        print("✅ BTC analysis delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
