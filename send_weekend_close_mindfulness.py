import requests
import json

def send_weekend_close_mindfulness():
    """Send the weekend close mindfulness post to Discord"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417721618028957696/2V-0LHWY8-irDO8JYKZenfN9xtAB0gIMbLLZwEL6zQWVM4juGaLfaKnQCaxIzJ-YKeNk"

    # The message content
    message_content = """🔮 **Third Eye | Weekend Close Mindfulness**

The candles are slowing down. Liquidity's fading. It's that space between exhaustion and reset—where real traders breathe while everyone else forces one more trade.

💭 **The Vibe:**
- Some are clutching profits, scared to give them back.
- Some are fighting red, hoping for a Friday miracle.
- The calm few are already done, protecting their energy for next week's real setups.

✨ **Guidance for the Weekly Close:**
- Don't try to "finish strong." Finish clean.
- You don't need to make more money—you need to keep the money you made.
- The market will bait you with last-minute fakeouts. Don't chase the noise.
- Reflect before you reset. What did you learn this week about your patience, not your PnL?

📍 **Third Eye Reset Drill:**
Inhale 4 • Hold 4 • Exhale 8
Say: "I close the week steady. My clarity carries forward."

⚖️ **Rules for the Close:**
1️⃣ If you're green, stop trading. Protect it.
2️⃣ If you're red, accept it. Revenge never heals it.
3️⃣ Plan your zones and your bias for next week—don't guess.

🧠✨ The vibe tonight: quiet, grounded, proud of your discipline.
You showed up, stayed sharp, and lived to trade another week.
*Third Eye—ending the week with focus, peace, and precision.*"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🧘 Sending Weekend Close Mindfulness to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord weekend close mindfulness sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ Weekend close mindfulness delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_weekend_close_mindfulness()






























