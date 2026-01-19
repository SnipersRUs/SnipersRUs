#!/usr/bin/env python3
"""
Discord Webhook Script for BTC Weekend Game Plan
Sends announcement with @everyone ping to Discord channel
"""

import requests
import json
import sys

def send_discord_message():
    """Send the BTC weekend game plan to Discord with @everyone ping"""
    
    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"
    
    # The message content with @everyone ping (ultra-short for Discord 2000 char limit)
    message_content = """@everyone
**BTC WEEKEND GAME PLAN - Sniper Guru**

**TL;DR**
• Structure: Up-channel HTF, LTF spike to 121k then mean-reverted to 119-120k. Sitting under resistance.
• Bias: Neutral->Bull if 120.6-121.0k accepted. Bearish to 117s if 119.0k fails.
• Best sessions: Fri NY 9:30-11:30 ET, 14:00-16:00 ET. Sunday CME 18:00-22:00 ET. Avoid Saturday.

**KEY LEVELS**
• R: 120.6-121.0k (decision) -> 122.5k -> 124.0k
• Pivot: 119.2-119.6k (VWAP/POC)
• S: 118.5k -> 117.3k -> 116.5k -> 115.0k
• HTF S: 113.0-113.3k -> 112.7k -> 110.86k

**SETUPS**
**A) Breakout LONG**
• Trigger: 1H close >= 120.6-121.0k + hold above retest
• Entry: 120.8-121.2k on retest
• Stops: 119.9k (tight) or 119.2k (swing)
• Targets: 122.5k -> 124.0k

**B) Rejection SHORT**
• Trigger: Wick into 120.6-121.0k with rejection
• Entry: 120.4-120.8k
• Invalidation: 121.2k clean acceptance
• Targets: 119.6k -> 119.2k -> 118.5k

**C) Mean-revert LONG**
• Trigger: Sweep into 118.5k or 117.3k with absorption
• Entry: 118.6-118.9k or 117.3-117.6k
• Invalidation: 117.0k or 116.2k
• Targets: 119.6k -> 120.2k -> 120.6k

**WEEKEND PLAN**
• If 121k ACCEPTED -> bias Bull. Sunday: shallow pullback buys 120.6-121.0k -> 122.5-124k
• If 121k REJECTED <119.2k -> bias Range/Bear. Sunday: hunt CME gap reversion 118.5k/117.3k

**NEWS TO WATCH**
• NFP Fri 08:30 ET - expect volatility, first move can be fake
• ISM Services PMI today 10:00 ET - secondary vol after NFP
• FTX creditor distribution ~$1.6B began Sept 30

**Invalidations**
• Bull thesis invalid if lose 117.3k and can't reclaim next hour
• Bear thesis invalid if accept and hold above 121.0k

Stay sharp. Trade the reaction, not the prediction. - SG"""

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
            print("✅ Discord message sent successfully!")
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
    print("🚀 Sending BTC Weekend Game Plan to Discord...")
    print("=" * 50)
    
    success = send_discord_message()
    
    if success:
        print("=" * 50)
        print("✅ Mission accomplished! Check your Discord channel.")
    else:
        print("=" * 50)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)
