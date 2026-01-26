import requests
import json

def send_btc_weekend_update():
    """Send the BTC weekend update Part 1 to Discord"""

    # Discord webhook URL
    webhook_url = ""

    # Part 1 - First portion of the message
    message_content = """@everyone
**BTC WEEKEND UPDATE | Cloudfare™ + Sniper Breakdown**

## 🎯 @RickySpanish Bias
**Not fully bearish** yet. Structure held after flush. Drop might've been **reset at highs** before next move.

Near **105k spiderline**, bounced inside **Cloudfare cloud** (bulls/bears battle zone). **Neutral** - waiting for cloud reaction.

**Plan:**
- **Break above + back-test cloud** = bulls control → longs
- **Reject off cloud top** = sellers control → shorts
- **Liquidation candle** = sellers dominated OR buyers defended hard

Still **hope** - might've been **shakeout before real move**.

## ⚔️ Sniper Guru Add-On
**Potential bullish recovery pattern** forming (early).

### 🟩 The Cloud
- **Inside** = neutral/undecided
- **Above** = bullish (buyers control)
- **Below** = bearish (sellers control)
- Bitcoin **inside cloud** = decision zone

### 📊 VWAP Stack
- **VWAP Stack Bull** = all VWAPs below price
- **VWAP Stack Bear** = all VWAPs above price
- This week: VWAP stack **flattening** = before big moves

## 🧭 What's Happening
- **$10k+ drop** = liquidation reset
- **Historically**: 10-15% bounce within week if key support holds
- **2-Day chart**: strong trendline bounce (April 2023/March 2024 signature)

## 🧩 Key Levels
**126k** = Local top (reclaim = strength)
**120.5k** = Cloud breakout (above = bulls control)
**117-119k** = Battle zone (inside cloud = indecision)
**112-114k** = Key support (break = bearish)
**105k** = Spiderline (bounce zone)
**99k** = Macro pivot (below = bear market)

**Part 1/3 - Continued...**"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "Sniper Guru",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("📈 Sending BTC Weekend Update to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord BTC weekend update sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ BTC weekend update delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_btc_weekend_update()
