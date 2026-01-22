#!/usr/bin/env python3
"""
Send Zoomex referral link to Discord and reset daily posting schedule
"""

import requests
import json
import os
from datetime import datetime, timezone, timedelta

# Zoomex referral link
ZOOMEX_REF_LINK = "https://www.zoomex.com/en-US/feediscount?params=ref=0VL4Z8G%7CID=1c2e380a-836b-415c-ade1-cdbfb7b2c674%7CactUserId=524534287%7CactUserName=rickytspanish%E2%80%8B@gmail.com"

# Discord webhook (default from bounty_seeker_kcex.py)
default_webhook = ""
webhook = os.getenv("DISCORD_WEBHOOK", default_webhook).strip()
if not webhook or webhook == " ":
    webhook = default_webhook
# Check for .webhook file
if os.path.exists(".webhook"):
    try:
        file_webhook = open(".webhook").read().strip()
        if file_webhook:
            webhook = file_webhook
    except:
        pass

# Referral state path
REFERRAL_STATE_PATH = "referral_state.json"

# Card color (blue)
COLOR_BLUE = 0x3498DB

def send_zoomex_referral():
    """Send Zoomex referral card to Discord"""

    card = {
        "title": "Need an account to trade?",
        "description": f"[**Zoomex**]({ZOOMEX_REF_LINK})",
        "color": COLOR_BLUE,
        "url": ZOOMEX_REF_LINK
    }

    payload = {"embeds": [card]}

    try:
        response = requests.post(webhook, json=payload, timeout=15)

        if response.status_code in [200, 204]:
            print("✅ Zoomex referral card sent to Discord!")
            return True
        else:
            print(f"❌ Failed to send. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending referral card: {e}")
        return False

def reset_referral_state():
    """Reset referral state so it will post again tomorrow"""
    # Set yesterday's date so it will post today
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    try:
        with open(REFERRAL_STATE_PATH, "w") as f:
            json.dump({"last_post_date": yesterday}, f)
        print(f"✅ Referral state reset (last_post_date set to yesterday: {yesterday})")
        print("   Bot will post referral again on next run (once per day)")
        return True
    except Exception as e:
        print(f"⚠️ Could not reset referral state: {e}")
        print("   (This is okay if the file doesn't exist yet)")
        return False

if __name__ == "__main__":
    print("🚀 Sending Zoomex Referral Card to Discord...")
    print("=" * 50)

    # Send the referral card
    success = send_zoomex_referral()

    # Reset the state so it will post again tomorrow
    reset_referral_state()

    print("=" * 50)
    if success:
        print("✅ Done! Referral card sent and daily schedule reset.")
        print("   The bot will automatically post the referral link once per day.")
    else:
        print("⚠️ Referral card may not have been sent. Check errors above.")
