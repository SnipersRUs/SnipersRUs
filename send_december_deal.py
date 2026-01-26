#!/usr/bin/env python3
"""
Send December Deal Announcement to Discord webhook
"""

import requests
import time

WEBHOOK_URL = ""

MESSAGES = [
    """@everyone 🎯 **DECEMBER DEAL - LIMITED TIME!** 🎯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔥 **@bountyseeker Monthly Access**

**Regular:** $60/month
**DEAL:** **$40/month (LOCKED IN RATE!)**

This deal ends December 31st.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**What you get:**
• Everything in Headhunters (daily trades, indicators, analysis)
• Direct access to me personally
• Ask me questions anytime when I'm available
• See all trades I'm watching and taking
• My personal trades shared in real-time with entry/exit points and reasoning
• Cloudfare indicator included
• All current and future content

[Get Monthly Access ($40/month)](https://upgrade.chat/734621342069948446)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 **@bountyseeker Lifetime Access**

**Regular:** $60/month or $333 lifetime
**DEAL:** **$222 (one-time)**

This deal ends December 31st.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**What you get:**
• Permanent Bounty Hunter role status
• Everything in Headhunters (daily trades, indicators, analysis)
• Direct access to me personally
• Ask me questions anytime when I'm available
• See all trades I'm watching and taking
• My personal trades shared in real-time with entry/exit points and reasoning
• Cloudfare indicator included
• Complete access to ALL current and future content
• Never pay another monthly fee

[Get Lifetime Access ($222)](https://upgrade.chat/734621342069948446)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Take trades at your own discretion with our guidance.

**Questions?** DM me or ask in the server! 🚀"""
]

def send_message(content, delay=0.5):
    """Send a single message to Discord"""
    payload = {
        "content": content,
        "username": "Sniper Guru"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False
    finally:
        if delay > 0:
            time.sleep(delay)

def send_to_discord():
    """Send December deal message to Discord"""
    print("Sending December deal to Discord...")

    # Send single message
    if send_message(MESSAGES[0], delay=0):
        print("✅ December deal sent successfully to Discord!")
        return True
    else:
        print("❌ Failed to send December deal")
        return False

if __name__ == "__main__":
    send_to_discord()
