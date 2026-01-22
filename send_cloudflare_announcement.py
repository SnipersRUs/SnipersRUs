#!/usr/bin/env python3
"""
Discord Webhook Script for Cloudflare Announcement
Sends Cloudflare market sentiment scanner announcement to Discord channel
"""

import requests
import json
import sys

def send_cloudflare_announcement():
    """Send the Cloudflare announcement to Discord"""
    
    # Discord webhook URL
    webhook_url = ""
    
    # The Cloudflare announcement message content
    message_content = """Hey Snipers! 👋
After 3 months of development and testing, I'm finally ready to drop Cloudfare - the market sentiment scanner that's been my secret weapon!

🌟 **What Makes This Special?**

**The Cloud That Breathes** 💨
Watch the market literally "breathe" with our dynamic cloud system
Green cloud = Bullish money flow, Red cloud = Bearish pressure
The brighter it glows, the stronger the trend!
Built specifically for scalpers who need instant market reads

**Diamond Signals That Actually Work** 💎
Green diamonds = Bullish reversals (Higher High patterns)
Red diamonds = Bearish reversals (Lower Low patterns)
The brighter the diamond, the better the signal!

**Multi-Timeframe VWAP Stack** 📊
See exactly where institutions are positioned across multiple timeframes
Perfect for scalping entries and exits

🚀 **Why This Is Game-Changing:**
✅ No more guessing - the cloud tells you market sentiment instantly
✅ No more false signals - 5-day confirmation system filters the noise
✅ No more missing reversals - glowing diamonds show optimal entries
✅ Built for speed - instant visual confirmation for scalpers

💰 **Pricing:**
🔥 $40 ONE-TIME FEE for SnipersRUs members (Regular price: $125)
🔥 FREE for @BountySeeker holders
🔥 No subscriptions, no monthly fees, no BS!

🎁 **@BountySeeker Access:**
@BountySeeker holders - you have FREE access asap!
Just drop your TradingView handle and I'll get you set up immediately!

📈 **Perfect For:**
Scalpers who need instant market reads
Swing traders looking for high-probability setups
Anyone tired of lagging indicators
Traders who want to see market sentiment in real-time

This isn't just another indicator - it's your market edge!
The cloud literally shows you when money is flowing in or out. Once you see it, you'll never trade without it! 💪"""

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
            print("✅ Discord Cloudflare announcement sent successfully!")
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
    print("🚀 Sending Cloudflare Announcement to Discord...")
    print("=" * 60)
    
    success = send_cloudflare_announcement()
    
    if success:
        print("=" * 60)
        print("✅ Cloudflare announcement delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

































