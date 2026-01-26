import requests
import json

def send_mms_bot_explanation():
    """Send explanation of what the MMS bot does to Discord"""

    # Discord webhook URL
    webhook_url = ""

    # Part 1 of the MMS bot explanation
    message_content = """**🤖 MMS Bot - What It Does & How to Read It (Part 1/2)**

Hey Snipers! 👋

The **MMS (Market Monitoring System)** bot is now live and scanning BTC & SOL every 10 minutes.

## 🎯 **What This Bot Does**
- Scans BTC and SOL markets every 10 minutes
- Posts cards with real-time market analysis and trading opportunities
- Monitors your trades automatically and sends alerts when you enter/exit
- Tracks your performance with PnL summaries

## 📊 **How to Read the Cards**

### **🟢🟣⚪️ Bias Dots**
- **🟢 Green** = Bullish bias (price likely to go up)
- **🟣 Purple** = Bearish bias (price likely to go down)
- **⚪️ White** = Neutral (no clear direction)
- **M15 | H1 | H4** = Different timeframes (15min, 1hour, 4hour)

### **💰 Funding Rate**
- **Positive %** = Long-biased (people paying to hold long positions)
- **Negative %** = Short-biased (people paying to hold short positions)
- **Near 0%** = Neutral market

### **📈 Flow & Order Book**
- **CVD (Cumulative Volume Delta)** = Shows if more buying or selling pressure
- **OB Imb (Order Book Imbalance)** = Shows if more buyers or sellers at current price
- **Positive** = More buying pressure
- **Negative** = More selling pressure

### **📊 VWAP (Volume Weighted Average Price)**
- **Above VWAP** = Momentum (trending up)
- **Below VWAP** = Value (good buy zone)
- **VWAP bands** = Support/resistance levels

### **🧱 OB Walls (Order Book Walls)**
- **↓ Red arrows** = Big sell orders (resistance)
- **↑ Green arrows** = Big buy orders (support)
- **Magnet** = Which direction price is being pulled

**Continued in Part 2...**"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "MMS Bot",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🤖 Sending MMS Bot Explanation to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord MMS bot explanation sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ MMS bot explanation delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_mms_bot_explanation()
