#!/usr/bin/env python3
"""
Discord Webhook Script for Membership Tiers
Sends membership tiers announcement as a purple embed card to Discord
"""

import requests
import json
import sys

def send_membership_tiers():
    """Send the membership tiers announcement to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1438326547110035547/pRXOZkQnwNpB4V_1NschjbqxsveZL92ZpzKOwLFwKCgV_9jMZfVEqQtThhHOQit0XYCn"

    # Role IDs for mentions (clickable role links)
    HEADHUNTERS_ROLE_ID = "734627491548889088"
    # Bounty Seekers role ID - replace with actual role ID (format: "123456789012345678")
    # To find role ID: Right-click role in Discord > Copy ID (Developer Mode must be enabled)
    BOUNTY_SEEKERS_ROLE_ID = "734627491548889088"  # REPLACE THIS with actual Bounty Seekers role ID

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "SnipersRus Membership Tiers 🎯",
        "description": "Ready to level up your trading? Here's what each tier gets you:",
        "color": PURPLE_COLOR,
        "fields": [
            {
                "name": "🔹 <@headhunter> - $20/month",
                "value": (
                    "• 1-2 trades and analysis almost every day (depends on market structure and PA)\n"
                    "• Full access to trading indicators library\n"
                    "• Daily market analysis and trade ideas\n"
                    "• Member-only channels\n"
                    "• **Cloudfare indicator included**\n\n"
                    "Take trades at your own discretion with our guidance."
                ),
                "inline": False
            },
            {
                "name": "🔹 <@bountyseeker> - $40/month",
                "value": (
                    "Everything in Headhunters, PLUS:\n"
                    "• All access to me personally\n"
                    "• Ask me questions anytime when I'm available\n"
                    "• See all trades I'm watching and taking\n"
                    "• Know what I'll be looking for in the future\n"
                    "• My personal trades shared in real-time with entry/exit points and reasoning\n"
                    "• **Cloudfare indicator included**\n\n"
                    "**NEW: 3-Day Free Trial available!**"
                ),
                "inline": False
            },
            {
                "name": "🔹 Lifetime Membership - $333 (one-time)",
                "value": (
                    "• Permanent Bounty Hunter role status\n"
                    "• Complete access to ALL current and future content\n"
                    "• Never pay another monthly fee\n"
                    "• Best value for serious traders\n"
                    "• **Cloudfare indicator included**"
                ),
                "inline": False
            },
            {
                "name": "How to Join",
                "value": (
                    f"**[Headhunters ($20/month)](https://upgrade.chat/734621342069948446/p/ath)**\n"
                    f"**[Bounty Seekers ($40/month)](https://upgrade.chat/734621342069948446/p/e4097a76-84f4-4138-a754-f0cfaae66291)**\n"
                    f"**[Lifetime Membership ($333 one-time)](https://upgrade.chat/734621342069948446/p/lifetime)**"
                ),
                "inline": False
            },
            {
                "name": "Upon Purchase",
                "value": "You'll receive the appropriate role (<@headhunter> or <@bountyseeker>) and immediate access to your membership benefits.",
                "inline": False
            }
        ],
        "footer": {
            "text": "Ready to start executing precision trades? Join SnipersRus today! 🎯"
        }
    }

    # Discord webhook payload
    payload = {
        "embeds": [embed],
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ Discord membership tiers announcement sent successfully!")
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
    print("🚀 Sending Membership Tiers Announcement to Discord...")
    print("=" * 60)

    success = send_membership_tiers()

    if success:
        print("=" * 60)
        print("✅ Membership tiers announcement delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
