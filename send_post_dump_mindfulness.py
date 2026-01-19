#!/usr/bin/env python3
"""
Discord Webhook Script for Post-Dump Mindfulness
Sends mindfulness trading wisdom during market volatility with @everyone ping to Discord channel
"""

import requests
import json
import sys

def send_post_dump_mindfulness():
    """Send the post-dump mindfulness message to Discord with @everyone ping"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417721618028957696/2V-0LHWY8-irDO8JYKZenfN9xtAB0gIMbLLZwEL6zQWVM4juGaLfaKnQCaxIzJ-YKeNk"

    # The post-dump mindfulness message content with @everyone ping
    message_content = """@everyone
🔮 **Third Eye | Daily Mindfulness — Post-Dump Edition**

We woke up to red.
The same crowd that screamed "new highs" yesterday is quiet now.
This is where real traders start paying attention.

💭 **Market Sentiment:**
- Retail is nervous, thinking the run's over.
- Smart money is watching liquidity build under every wick.
- Vets aren't panicking—they're plotting. Dumps build opportunity.

✨ **Guidance for today:**
- Don't call bottoms—confirm them.
- Watch for reclaim candles and volume shifts; that's where reversals begin.
- If you're already long, breathe. React, don't flinch.
- If you're flat, good—this is where patience pays.

📍 **Mindfulness Drill:**
Inhale 4 • Hold 4 • Exhale 8
Say: "Fear is data. Patience is power."

⚖️ **Rules to carry:**
1️⃣ No catching knives—wait for structure to rebuild.
2️⃣ Lower liquidity = higher traps; fade noise, not trend.
3️⃣ Don't confuse volatility with opportunity.

🧠✨ **The vibe today:** calm, observant, hungry but controlled.
While others panic, you refine your plan.
*Third Eye—steady through the storm, waiting for the setup.*"""

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
            print("✅ Discord post-dump mindfulness sent successfully!")
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
    print("🧘 Sending Post-Dump Mindfulness to Discord...")
    print("=" * 60)

    success = send_post_dump_mindfulness()

    if success:
        print("=" * 60)
        print("✅ Post-dump mindfulness delivered! Check your Discord channel.")
    else:
        print("=" * 60)
        print("❌ Failed to send message. Check the error above.")
        sys.exit(1)

































