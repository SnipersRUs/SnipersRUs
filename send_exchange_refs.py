#!/usr/bin/env python3
"""
Discord Webhook Script for Exchange Referral Links
Sends referral links for Bitunix and Zoomex exchanges
"""

import requests
import sys

def send_exchange_refs():
    """Send exchange referral links to Discord as a purple embed card"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1438335989507686553/omLFMLZdWsglW2ruQ02cQUEkKeDpJkBlopmqL3gzW2r53Kl2RJd9By78Apaf9E_QzC8S"

    # Referral links
    bitunix_ref = "https://www.bitunix.com/register?inviteCode=3vm3p7"
    zoomex_ref = "https://www.zoomex.com/en-US/feediscount?params=ref=0VL4Z8G%7CID=1c2e380a-836b-415c-ade1-cdbfb7b2c674%7CactUserId=524534287%7CactUserName=rickytspanish%E2%80%8B@gmail.com"

    # Purple color for embed
    PURPLE_COLOR = 0x8E44AD

    # Create the embed
    embed = {
        "title": "Exchange Referral Links 🎯",
        "description": (
            "If anyone is looking for an exchange to trade on! Here are my two ref links:\n\n"
            f"**[Bitunix]({bitunix_ref})**\n"
            f"**[Zoomex]({zoomex_ref})**"
        ),
        "color": PURPLE_COLOR,
        "footer": {
            "text": "Start trading with these exchanges today!"
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
            print("✅ Discord exchange referral links sent successfully!")
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
    print("🚀 Sending Exchange Referral Links to Discord...")
    print("=" * 60)

    success = send_exchange_refs()

    if success:
        print("=" * 60)
        print("✅ Exchange referral links delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
