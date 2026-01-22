#!/usr/bin/env python3
"""
Discord Webhook Script for Server Disclaimer
Sends the server disclaimer and guidelines to Discord
"""

import requests
import sys

def send_server_disclaimer():
    """Send the server disclaimer to Discord"""

    # Discord webhook URL
    webhook_url = ""

    # Message content
    message_content = """We want to create a safe and supportive learning environment in this Discord server. If you have any questions or concerns, please do not hesitate to ask. We are here to help and support you in your learning journey. Our moderators and members @oathkeepers are here to help and are happy to share their knowledge and experiences with you.

**Important Disclaimer:**

The information provided in this Discord server is for **educational purposes only** and should **NOT** be considered as professional financial advice. **NFA (Not Financial Advice)**.

Any trades, investments, or financial decisions you make based on information shared in this group are **solely at your own risk**. We strongly recommend that you:

• **DYOR (Do Your Own Research)** before making any financial decisions
• Seek professional financial advice from qualified advisors
• Never invest more than you can afford to lose
• Understand that trading involves substantial risk of loss

The moderators, members, and administrators of this server are not licensed financial advisors, and nothing shared here constitutes financial, investment, or trading advice.

We hope you enjoy your learning experience here in SnipersRUs!"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru"
    }

    try:
        # Send the webhook request
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 204:
            print("✅ Discord server disclaimer sent successfully!")
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
    print("🚀 Sending Server Disclaimer to Discord...")
    print("=" * 60)

    success = send_server_disclaimer()

    if success:
        print("=" * 60)
        print("✅ Server disclaimer delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

