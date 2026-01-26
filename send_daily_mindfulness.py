#!/usr/bin/env python3
"""
Discord Webhook Script for Daily Mindfulness Check-In
Sends mindfulness trading wisdom with @everyone ping to Discord channel
"""

import requests
import json
import sys

def send_daily_mindfulness():
    """Send the daily mindfulness check-in to Discord with @everyone ping"""
    
    # Discord webhook URL
    webhook_url = ""
    
    # The daily mindfulness message content with @everyone ping
    message_content = """@everyone
🔮 **Third Eye | Daily Mindfulness Check-In**

Today feels heavy but focused.  
The hype is fading, the noise is thinning, and traders are quietly trying to figure out what's next.  

💭 **The energy right now:**
- Some are still chasing yesterday's momentum.  
- Some are waiting for the inevitable pullback.  
- The smart ones are doing what they always do—staying patient, planning the next clean strike.  

✨ **Guidance for today:**
- You don't have to outsmart the market; you just have to outwait the crowd.  
- Watch volume and structure—let price show you where real strength sits.  
- If you missed the move, don't chase the top; let it breathe, then join the next setup.  
- Protect your mental capital—tired traders make emotional trades.  

📍 **Mindfulness Drill:**
Inhale 4 • Hold 4 • Exhale 8  
Say: "I move with calm precision. The market moves; I respond."  

⚖️ **Rules to carry:**
1️⃣ Trade less, think more.  
2️⃣ Wait for your levels; don't let price drag you out of position.  
3️⃣ One trade done right is better than ten trades done emotional.  

🧠✨ **The mood:** calm eyes, steady breath, focused mind.  
We don't chase days like this—we read them, wait, and strike when the edge aligns.  
*Third Eye—balanced in motion, grounded in discipline.*"""

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
            print("✅ Discord daily mindfulness sent successfully!")
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
    print("🧘 Sending Daily Mindfulness Check-In to Discord...")
    print("=" * 60)
    
    success = send_daily_mindfulness()
    
    if success:
        print("=" * 60)
        print("✅ Daily mindfulness delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

































