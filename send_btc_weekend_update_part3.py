import requests
import json
import time

def send_btc_weekend_update_part3():
    """Send the BTC weekend update Part 3 to Discord"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417680286921134251/qP3_kjOWd3UvXSyv27UXjO7HTzqLx9AhfVlLalkyE3DQrmmKtR99UwE-NGvEu9KIHClO"

    # Part 3 - Final thoughts and links
    message_content = """**BTC WEEKEND UPDATE | Part 3/3**

## 📘 For New Traders Following Along

**Cloudfare Indicator Recap:**
- 🟩 **Green Cloud** = Bullish momentum
- 🟥 **Red Cloud** = Bearish momentum
- 🟨 **Inside Cloud** = Neutral zone
- ▲ = Pre-Bull signal (potential bounce forming)
- ▼ = Pre-Bear signal (potential rejection forming)
- 🏳️ = Confirmed trend change (bull or bear depending on color)
- 💡 Tip: Don't trade just because you see a symbol — wait for confirmation near key levels.

## 💬 Final Thoughts

🔸 **@RickySpanish** is neutral, leaning cautiously bullish as long as structure holds.
🔸 **Sniper Guru** sees the same — potential for recovery if 112–113k support holds & we reclaim the cloud.
🔸 The market just went through one of the biggest liquidation events of the year — those often mark major turning points.

Stay patient, don't overtrade the weekend, and let the cloud guide the bias.
Sunday night's reopen will tell us everything we need to know going into next week.

**Add Cloudfare on your TradingView charts** to follow these setups live:
👉 https://www.tradingview.com/script/ZWA48gFW-Cloudfare/

Keep your scopes steady, Snipers. 🎯"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("📈 Sending BTC Weekend Update Part 3 to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord BTC weekend update Part 3 sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ BTC weekend update Part 3 delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_btc_weekend_update_part3()






























