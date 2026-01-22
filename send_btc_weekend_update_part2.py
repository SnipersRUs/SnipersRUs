import requests
import json
import time

def send_btc_weekend_update_part2():
    """Send the BTC weekend update Part 2 to Discord"""

    # Discord webhook URL
    webhook_url = ""

    # Part 2 - Strategy and timing
    message_content = """**BTC WEEKEND UPDATE | Part 2/3**

## 🧠 Strategy
**1️⃣ Break 120.5k + hold** = bullish → 122.5k → 124.2k → 126k
**2️⃣ Fail 120k + reject** = bearish → shorts 119.8-120.6k → 116.9k → 113k
**3️⃣ Dip 113k + hold** = trendline bounce → volume + ▲ Pre-Bull = entry

## 🕒 Timing
- **Avoid Saturdays** (low liquidity)
- **Best**: Fri NY 9:45-11:15 AM & 1:45-3:30 PM ET, Sun night/Mon Asia 8 PM-2 AM UTC

## 📰 Sentiment
- **Macro**: Trump tariffs, gov funding, equity pullbacks
- **Crypto still hedge** if inflation sticky
- **"Uptober" not dead**: Early-Oct selloffs reset before mid-month runs

## 🧩 Cloudfare Signals
- **🟩 Green Cloud** = Bullish momentum
- **🟥 Red Cloud** = Bearish momentum
- **🟨 Inside Cloud** = Neutral zone
- **▲ Pre-Bull** = Potential bounce
- **▼ Pre-Bear** = Potential rejection
- **🏳️ Bull/Bear Confirm** = Confirmed trend change

## 💬 Final Thoughts
🔸 **@RickySpanish**: Neutral, cautiously bullish if structure holds
🔸 **Sniper Guru**: Recovery potential if 112-113k support + cloud reclaim
🔸 **Biggest liquidation event of year** = major turning points

Stay patient, don't overtrade weekend, let cloud guide bias.
Sunday night's reopen will tell us everything.

**Part 2/3 - Continued...**"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("📈 Sending BTC Weekend Update Part 2 to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord BTC weekend update Part 2 sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ BTC weekend update Part 2 delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_btc_weekend_update_part2()
