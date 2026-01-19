import requests
import json

def send_mms_bot_explanation_part2():
    """Send Part 2 of the MMS bot explanation to Discord"""

    # Discord webhook URL
    webhook_url = "https://discord.com/api/webhooks/1417096846978842634/__rOUU6qOz_mRIRO2MUG8PpR4BMyTpmONQ9PDIpB21z47k5pKDbBbSjj3AKciiHsOCq8"

    # Part 2 of the MMS bot explanation
    message_content = """**🤖 MMS Bot - Part 2/2**

### **💥 Liquidations**
- **↑ Nearest Up** = Next short liquidation level (price target)
- **↓ Nearest Down** = Next long liquidation level (price target)
- **Clusters** = Where most liquidations happened recently

### **⚡ Scalp Watch**
- **LONG/SHORT** = Suggested direction
- **Entry** = Price to enter the trade
- **TP1/TP2** = Take profit levels (partial and full)
- **Stop** = Stop loss level
- **Prob %** = Probability of success
- **R:R** = Risk to reward ratio

## 🚨 **Trade Alerts**
- **⚡ Entry** = Bot detected your entry price hit
- **✅ WIN** = Trade hit take profit
- **⛔️ LOSS** = Trade hit stop loss
- **📊 PnL Card** = Shows your last 5 trades with win/loss record

## 💡 **Pro Tips**
- **Green bias + above VWAP** = Strong bullish setup
- **Purple bias + below VWAP** = Strong bearish setup
- **High probability %** = Better setups (70%+ is good)
- **Watch liquidations** = They often mark turning points
- **Use the TradingView links** = Click to see the charts

## ❓ **Need More Help?**
- **Screenshot any card** and ask your AI chat bot to explain it further
- **@RickySpanish** for specific questions about the bot
- **Don't trade everything** - only take high-probability setups!

**Remember**: This bot gives you information, but YOU make the trading decisions. Always manage your risk! 🎯"""

    # Discord webhook payload
    payload = {
        "content": message_content,
        "username": "MMS Bot",
        "avatar_url": "https://i.imgur.com/YOUR_AVATAR_URL.png" # Optional: Replace with a suitable avatar URL
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🤖 Sending MMS Bot Explanation Part 2 to Discord...")
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status() # Raise an exception for HTTP errors
        print("============================================================")
        print(f"✅ Discord MMS bot explanation Part 2 sent successfully!")
        print(f"📊 Message length: {len(message_content)} characters")
        print("============================================================")
        print("✅ MMS bot explanation Part 2 delivered! Check your Discord channel.")
    except requests.exceptions.RequestException as e:
        print("============================================================")
        print(f"❌ Failed to send Discord message. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("============================================================")
        print(f"❌ Failed to send message. Check the error above.")

if __name__ == "__main__":
    send_mms_bot_explanation_part2()























