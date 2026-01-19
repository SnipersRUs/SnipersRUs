#!/usr/bin/env python3
"""
Discord Webhook Script for Black Friday Bounty Seeker Deal
Sends Black Friday lifetime membership deal announcement to Discord
"""

import requests
import json
import sys

def send_black_friday_deal():
    """Send the Black Friday Bounty Seeker deal announcement to Discord"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

    # Black Friday deal link
    BLACK_FRIDAY_LINK = "https://upgrade.chat/734621342069948446/p/722e1328-96f8-47b8-ab73-e076f33d77f2"

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "Black Friday Deal - @bountyseeker Lifetime Access",
        "description": "@bountyseeker role lifetime access: **$111 (one-time)**\n\nRegular price is $60/month or $333 lifetime. This deal ends December 1st.",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "What's included:",
                "value": (
                    "• Everything in Headhunters (daily trades, indicators, analysis)\n"
                    "• Direct access to me personally\n"
                    "• Ask questions anytime when I'm available\n"
                    "• See all trades I'm watching and taking\n"
                    "• My personal trades shared in real-time with entry/exit points and reasoning\n"
                    "• Cloudfare indicator included\n"
                    "• All current and future content"
                ),
                "inline": False
            },
            {
                "name": "Link:",
                "value": f"[Get Lifetime Access]({BLACK_FRIDAY_LINK})",
                "inline": False
            }
        ],
        "footer": {
            "text": "Take trades at your own discretion with our guidance."
        }
    }

    # Discord webhook payload
    payload = {
        "content": "hey snipers @here",
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ Discord Black Friday announcement sent successfully!")
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
    print("🚀 Sending Black Friday Bounty Seeker Deal to Discord...")
    print("=" * 60)

    success = send_black_friday_deal()

    if success:
        print("=" * 60)
        print("✅ Black Friday announcement delivered! Check your Discord channel.")
        print("\n⚠️  REMINDER: Update the BLACK_FRIDAY_LINK variable with your actual upgrade.chat link!")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
