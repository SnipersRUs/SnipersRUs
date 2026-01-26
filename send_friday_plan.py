import requests
import json

def send_friday_plan():
    """Send the Friday plan to Discord"""

    # Discord webhook URL
    webhook_url = ""

    # The Friday plan message content (ultra-condensed for Discord 2000 char limit)
    message_content = """**FRIDAY PLAN — OCT 10, 2025**
**BTC into weekend close | Fast news + clean setups**

**CONTEXT**
• Mid-week shakeout bounce from ~121k, oscillating under VWAP with lower highs on LTFs
• HTF up-channel intact; daily momentum cooled but not broken. Weekend flow thin—expect fake moves
• Macro: PPI + jobless claims today, U. Michigan sentiment later. CPI next week—respect event risk
• Geo: ceasefire talks (Middle East), Ukraine strikes. Risk tone: cautious but not risk-off
• Expect squeeze into resistance OR controlled drift to next demand. Trade confirmation, not guess

**KEY LEVELS**
• R: 122.9k → 123.6k → 124.4k
• Pivot: 122.2k–122.5k (VWAP battles)
• S: 121.6k–121.9k → 120.7k–120.1k
• Risk line: <119.9k = de-risk

**PROBABILITIES**
• Squeeze then fade (123.6k–124.4k): 45%
• Range-to-down (121.6k/120.7k test): 40%
• Full dump: 15%

**PLAYBOOK**

**1) VWAP RECLAIM LONG**
• Trigger: 15m close >122.4k, retest holds
• Entry: 122.45k–122.55k | Stop: 121.95k
• TPs: 123.20k → 123.95k → 124.60k

**2) SWEEP-LIFT LONG**
• Trigger: Sweep 121.6k–121.9k, reclaim 122.0k
• Entry: 121.8k | Stop: 121.25k
• TPs: 122.8k → 123.5k → 124.2k

**3) FADE SHORT**
• Trigger: Reject 122.9k–123.6k + div
• Entry: 123.3k | Stop: 123.95k
• TPs: 122.4k → 121.9k → 120.9k

**ETH & SOL**
• ETH: >3.38k bullish, reclaim 3.45k → 3.55k/3.62k | <3.33k range
• SOL: >195 → 201/205 | <192 mean-revert

**RISK RULES**
• 0.5–1% per idea. 3-strike rule
• Partial +0.8R. Trail VWAP/HL
• No unhedged swings into CPI week

**WEEKEND**
• Saturday = chop. Best: late Sat → Sun Asia + Sun NY handoff
• Mid-range = stand down, wait for VWAP reclaims/sweeps

**COMMUNITY**
Indicators: https://snipersrus.github.io/SnipersRUs/
@bountyseeker: $60/mo, 3-day trial

**BOTTOM LINE**
Trade VWAP reclaim or sweep-lift. <121.4k no reclaim → defensive 120.7k. Patience first, precision second."""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("📈 Sending Friday Plan to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord Friday plan sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ Friday plan delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_friday_plan()
