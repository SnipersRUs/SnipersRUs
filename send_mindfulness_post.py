#!/usr/bin/env python3
"""
Discord Webhook Script for Weekend Trading Mindfulness Post
Sends mindfulness post with @everyone ping to Discord channel
"""

import requests
import json
import sys

def send_mindfulness_post():
    """Send the weekend trading mindfulness post to Discord with @everyone ping"""
    
    # Discord webhook URL
    webhook_url = ""
    
    # The mindfulness message content with @everyone ping
    message_content = """@everyone
🔮 **Third Eye | Weekend Trading Mindfulness**

📉 Saturday isn't built for traders. Liquidity dries up, big players step aside, and what's left is chop. Chop eats patience, eats stops, eats accounts. Most traders lose more on Saturdays than they ever win.  

✨ **Why not trade Saturday:**
- No fresh order flow → just bots and small fish pushing price sideways.  
- Fake breakouts are the norm → they pull you in, then bleed you out.  
- Every setup feels forced → because the market isn't truly moving.  

📈 **Where to look instead:**
- Late Sunday → liquidity starts creeping back in as Asia and futures desks prepare.  
- Sunday night into Monday → real levels form, real money returns, and trades mean something.  

🧠 **Headspace for the weekend:**
You don't have to be in the market 7 days a week. Real traders know when *not* to trade. Flat is a position. Rest is a position. Discipline is the edge.  

📍 **Mindfulness Drill:**
Inhale 4 • Hold 4 • Exhale 8  
Say: "I don't chase chop. I wait for clarity."  

✨ **Inspiration:**
Don't waste bullets in the mud. Save them for when the ground is firm and the targets are clear. That's how pros play the game."""

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
            print("✅ Discord mindfulness post sent successfully!")
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
    print("🧘 Sending Weekend Trading Mindfulness Post to Discord...")
    print("=" * 60)
    
    success = send_mindfulness_post()
    
    if success:
        print("=" * 60)
        print("✅ Mindfulness post delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)


































