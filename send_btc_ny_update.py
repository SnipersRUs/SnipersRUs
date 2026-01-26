#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Quick NY Update
Sends BTC trading update to Discord
"""

import requests
import sys

def send_btc_ny_update():
    """Send the BTC Quick NY update to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = ""

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "BTC Quick NY update — VWAPs & plan 🎯",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "Bias",
                "value": "Neutral-to-cautiously bullish only if price reclaims 112–115k VWAP cluster. Otherwise lean short on rejections.",
                "inline": False
            },
            {
                "name": "Key Levels",
                "value": (
                    "• **Resistance / VWAP cluster:** 112k — 115k\n"
                    "• **Immediate support:** 109k — 108k\n"
                    "• **Lower structure:** 105k / 100k"
                ),
                "inline": False
            },
            {
                "name": "1) Bull Scenario (clean reclaim 112–115k)",
                "value": (
                    "• Entry: retest 112–114k\n"
                    "• Stop: <110k\n"
                    "• Targets: 116–118k / 122–125k\n"
                    "• Prob ~40%"
                ),
                "inline": False
            },
            {
                "name": "2) Short Fade (rejection at 113–115k)",
                "value": (
                    "• Entry: short on clear rejection / false break\n"
                    "• Stop: >116.5k\n"
                    "• Targets: 108–109k / 105k / 100k\n"
                    "• Prob ~35%"
                ),
                "inline": False
            },
            {
                "name": "3) Range Scalp (108–115k)",
                "value": (
                    "• Long near 108–109k | Short near 114–115k\n"
                    "• Keep small size, tight stops"
                ),
                "inline": False
            },
            {
                "name": "News to Watch",
                "value": "Producer Price data and Fed-related calendar items this week — treat any surprise as a volatility driver.",
                "inline": False
            },
            {
                "name": "Execution Rules",
                "value": "No FOMO, scale in on HTF confirmation (1H), tighten stops through news events.",
                "inline": False
            },
            {
                "name": "If Trading London",
                "value": "Watch early liquidity at 108–109k — if that fails, momentum short into US open likely. If dominance continues up, favor BTC over alts.",
                "inline": False
            }
        ],
        "footer": {
            "text": "Stay sharp. Trade the reaction, not the prediction."
        }
    }

    # Discord webhook payload
    payload = {
        "content": "@everyone",
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ BTC Quick NY update sent successfully!")
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
    print("🚀 Sending BTC Quick NY Update to Discord...")
    print("=" * 60)

    success = send_btc_ny_update()

    if success:
        print("=" * 60)
        print("✅ BTC update delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
